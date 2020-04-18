import json
import math
import os
import pprint
import re
import string
import sys
import traceback

from urllib.request import urlopen, Request
from datetime import datetime, timedelta
from random import shuffle

import MySQLdb
import requests
from bs4 import BeautifulSoup

from core import _conn, _cur, InitDB, Spotify

INFO = {
    "hot-100": {
        "chart": "hot-100",
        "url": "https://www.billboard.com/charts/hot-100/{}-{}-{}",
        "item_type": "track",
        "make_item": lambda t, a, r: SpotifyItem(t, a, r)
    },

    "billboard-200": {
        "chart": "billboard-200",
        "url": "https://www.billboard.com/charts/billboard-200/{}-{}-{}",
        "item_type": "album",
        "make_item": lambda t, a, r: SpotifyItem(t, a, uri=r["uri"])
    }
}


def sql_prep(s):
    return "NULL" if s is None else \
        "'%s'" % s.strip().replace("\\", "").replace("\'", "\\\'") \
        if isinstance(s, str) else "%s" % s


class SpotifyItem:
    def __init__(self, title=None, artist=None, search_result=None, uri=None):
        self.details = {
            "bb_artist": artist,
            "bb_title": title
        }

        if uri:
            album = Spotify().album(uri)
            self.details.update({
                "uri": uri,
                "spoffy_artist": album["artists"][0]["name"],
                "spoffy_title": album["name"],
                "popularity": album["popularity"],
                "duration": sum(track["duration_ms"] for track
                                in album["tracks"]["items"]),
                "genres": ",".join(album["genres"])
            })
        else:
            self.album_uri = search_result["album"]["uri"]
            self.album_type = search_result["album"]["album_type"]
            self.details.update({
                "uri": search_result["uri"],
                "spoffy_artist": search_result["artists"][0]["name"],
                "spoffy_title": search_result["name"],
                "popularity": search_result["popularity"],
                "duration": search_result["duration_ms"],
                "album_id": None
            })

    def getKeys(self):
        return ",".join(x for x in self.details.keys()
                        if self.details[x] is not None)

    # TODO: this should NOT be calling an external function
    def getValues(self):
        return ",".join(map(sql_prep, [x for x in self.details.values()
                                       if x is not None]))

    def __str__(self):
        return str(self.details)

######################

#datetime(2020, 3, 14)


def scrape(day=datetime(2020, 3, 14), end_year=1957):
    global _conn, _cur
    _conn, _cur = InitDB()

    while day.year > end_year:
        try:
            add_bb_entry(get_from_page(
                INFO["hot-100"], day), day, INFO["hot-100"])
            add_bb_entry(get_from_page(
                INFO["billboard-200"], day), day, INFO["billboard-200"])
            day -= timedelta(7)
        except Exception as e:
            print(e)
            traceback.print_exc(file=sys.stdout)
            continue


def get_from_page(info, day):
    print(day)

    day_url = info["url"].format(day.year, format(
        day.month, '02'), format(day.day, '02'))
    raw_html = urlopen(Request(
        day_url, headers={'User-Agent': 'Mozilla/5.0'}))
    page_soup = BeautifulSoup(raw_html, "html.parser")

    print(day_url)
    return extract_item_info(page_soup)


def extract_item_info(page):
    def html_to_dict(html): return {
        'title': html[0].getText(),
        'artist': html[1].getText()
    }

    x = json.loads(page.find("div", id="charts")['data-charts'])
    items = [{'title': y['title'], 'artist': y['artist_name']} for y in x]
    return items


def get_and_add_id(item_type, title, artist, info):
    global _conn, _cur
    select = "SELECT id, bb_title, bb_artist, spoffy_title, spoffy_artist \
	 	from {0}s where bb_title = {1} and bb_artist {2}" \
            .format(item_type, sql_prep(title),
                    ("=" + sql_prep(artist)) if artist is not None else " is NULL")
    _cur.execute(select)
    id = _cur.fetchall()

    # Add this item if it's not here already.
    if not id:
        item = search_item(title, artist, info)

        if "uri" in item.details and \
                not (item_type == "track" and item.album_type == "single"):
            alb_select = "SELECT id, bb_title, bb_artist, \
				spoffy_title, spoffy_artist \
				from albums where (spoffy_title = %s and spoffy_artist %s)"

            # If this is an album, make sure I add bb name to it.
            if item_type == "album":
                alb_select = alb_select % (
                    sql_prep(item.details["spoffy_title"]),
                    ("=" + sql_prep(item.details["spoffy_artist"])) if
                    artist is not None else " is NULL")

            # If this is a track, make sure the album exists too.
            elif item_type == "track":
                album_item = SpotifyItem(uri=item.album_uri)
                alb_select = alb_select % (
                    sql_prep(album_item.details["spoffy_title"]),
                    ("=" + sql_prep(album_item.details["spoffy_artist"])) if
                    artist is not None else " is NULL")

            _cur.execute(alb_select)
            alb_id = _cur.fetchall()

            # If the album doesn't exist at all, add it.
            if item_type == "track":
                if alb_id:
                    item.details["album_id"] = alb_id[0][0]
                else:
                    add_item(album_item, "album")
                    _cur.execute(alb_select)
                    item.details["album_id"] = _cur.fetchall()[0][0]

            # If the album is missing bb names, add them.
            elif alb_id and not alb_id[0][1]:
                alb_update = "UPDATE albums SET bb_title = %s, bb_artist = %s \
						WHERE spoffy_title = %s and spoffy_artist %s" % \
                    (sql_prep(title), sql_prep(artist),
                     sql_prep(item.details["spoffy_title"]),
                     ("=" + sql_prep(item.details["spoffy_artist"])) if
                     artist is not None else " is NULL")
                _cur.execute(alb_update)

        add_item(item, item_type)
        _cur.execute(select)
        id = _cur.fetchall()

    return id[0][0]


def add_item(item, type):
    global _conn, _cur
    insert = "INSERT IGNORE INTO %ss (%s) VALUES (%s)" % \
        (type,
             item.getKeys(),
             item.getValues())
    _cur.execute(insert)
    return


def add_bb_entry(items, day, info):
    global _conn, _cur
    for i, item in enumerate(items):
        id = get_and_add_id(info['item_type'], item["title"], item["artist"],
                            info)
        week = "{}-{}-{}".format(day.year,
                                 format(day.month, "02"), format(day.day, "02"))
        _cur.execute("INSERT IGNORE INTO billboard.`%s` (week, idx, item_id) \
			VALUES ('%s', %s, %s)" % (info["chart"], week, i + 1, id))
        _conn.commit()


def remove_parens(s): return re.sub(r"\(.+\)|[.+]", "", s)


def has_bad_words(original, result, words):
    return any(word in original != word in result for word in words)


def get_query(title, artist):
    artist = " ".join(filter(
        lambda word: "feat" not in word
        and word not in string.punctuation and len(word) > 1,
        artist.lower().split()))

    return remove_parens(title) + " " + " ".join(artist.split()[:3])


def search_item(title, artist, info):
    title_bb = title.lower().strip()
    artist_bb = artist.lower().strip() if artist else ""
    query = get_query(title_bb, artist_bb)
    search_results = Spotify().search(
        q=query, type=info["item_type"], limit=50)

    failed = []
    for result in search_results[info["item_type"] + "s"]["items"]:
        item = remove_parens(result["name"].lower())
        if has_bad_words(title_bb, item, ["cover", "karaoke", "remix"]):
            continue

        artist_spoffy = result["artists"][0]["name"].lower()
        if has_bad_words(artist_bb, artist_spoffy, ["tribute", "karaoke"]):
            break

        if (LSSMatch(artist_bb, artist_spoffy) >= .75
                or artist_bb == "soundtrack") \
                and LSSMatch(item, title_bb) >= .75:
            return info["make_item"](title, artist, result)

        failed.append("\"%s\" by %s" % (item, result["artists"][0]["name"]))

    print("\"%s\" not found" % (query))
    for fail in failed[:5]:
        print("\t", fail)

    return SpotifyItem(title, artist)


def LSSMatch(one, two):
    shortest, longest = (one, two) if len(one) < len(two) else (two, one)

    if len(shortest) == 0:
        return 0

    matrix = [[0 for i in range(len(shortest) + 1)]
              for j in range(len(longest) + 1)]
    for x in range(1, len(longest) + 1):
        for y in range(1, len(shortest) + 1):
            matrix[x][y] = (matrix[x - 1][y - 1] + 1) \
                if longest[x - 1] == shortest[y - 1] \
                else max(matrix[x - 1][y], matrix[x][y - 1])

    return float(matrix[-1][-1]) / len(shortest)


def truncate_all():
    global _conn, _cur
    _cur.execute(
            "truncate albums; truncate `billboard-200`; truncate `hot-100`; \
		truncate tracks;")
    _cur.close()
    _cur = _conn._cursor()


def fill_in_uris():
    global _conn, _cur
    _cur.execute("SELECT * FROM songs where id not in (SELECT id FROM uris)")
    for song in _cur.fetchall():
        print(song)

        uri = get_song_link(song[1], song[2])
        if uri:
            newuri = "INSERT IGNORE INTO billboard.uris (id, uri, song, artist)\
				VALUES (%s, '%s', '%s', '%s')" \
                    % (song[0], uri["uri"], sql_prep(uri['title']),
                       sql_prep(uri['artist']))
            _cur.execute(newuri)
            _cur.execute("UPDATE billboard.songs SET song='%s', popularity = %s\
				where id = %s" % (song[1].replace("'", "\\'"),
                      uri["popularity"], song[0]))
            _conn.commit()


if __name__ == "__main__":
    scrape()
