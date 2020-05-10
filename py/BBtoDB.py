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

from core import select, insert, InitDB, Spotify

#datetime(2020, 3, 14)


def scrape(day=datetime(2020, 5, 9), end_year=1957):
    # TODO: set date to previous or current saturday?
    # TODO: figure out the day that it transitioned from some other day to Saturday
    while day.year > end_year:
        try:
            add_bb_entry(get_from_page(INFO["hot-100"], day), day, INFO["hot-100"])
        except Exception as e:
            print(e)
            traceback.print_exc(file=sys.stdout)

        try:
            add_bb_entry(get_from_page(INFO["billboard-200"], day), day,
                         INFO["billboard-200"])
        except Exception as e:
            print(e)
            traceback.print_exc(file=sys.stdout)

        day -= timedelta(7)


def get_from_page(info, day):
    day_url = info["get_url"](format_date(day))
    raw_html = urlopen(Request(day_url, headers={'User-Agent': 'Mozilla/5.0'}))
    page_soup = BeautifulSoup(raw_html, "html.parser")

    print("Trying day %s at url %" % (day, day_url))
    return extract_item_info(page_soup)


def extract_item_info(page):
    charts = json.loads(page.find("div", id="charts")['data-charts'])
    return [{'title': y['title'], 'artist': y['artist_name']} for y in charts]


def add_bb_entry(items, day, info):
    for i, item in enumerate(items):
        id = get_and_add_id(info['item_type'], item["title"], item["artist"], info)
        insert("INSERT IGNORE INTO billboard.`%s` (week, idx, item_id) \
		       VALUES ('%s', %s, %s)" % (info["chart"], format_date(day), i + 1, id))

def get_and_add_id(item_type, title, artist, info):
    select_id = "SELECT id, bb_title, bb_artist, spoffy_title, spoffy_artist \
	        	from %ss where bb_title = %s and bb_artist %s" \
                % map(sql_prep, [item_type, title,
                                 ("=" + sql_prep(artist)) if artist is not None\
                                  else " is NULL"])
    id = select(select_id)

    # Add this item if it's not here already.
    if not id:
        item = search_item(type, title, artist)

        # Add its associated album too
        # uri not in details means it wasn't found in search
        # tracks and singles shouldn't be added to the albums
        if item_type == "track" and item.album_type != "single" \
           and "uri" in item.details:
            album_item = SpotifyItem(type="album", title, artist, uri=item.album_uri)
            item.details["album_id"] = \
                get_and_add_id("album", album_item.details["spoffy_title"],
                               album_item.details["spoffy_artist"], info)

        insert("INSERT IGNORE INTO %ss (%s) VALUES (%s)" % \
               (item_type, item.getKeys(), item.getValues()))
        id = select(select_id)

    return id[0][0]

def remove_parens(s): return re.sub(r"\(.+\)|[.+]", "", s)

def format_date(day):
    return "{}-{}-{}".format(day.year, format(day.month, "02"),
                             format(day.day, "02"))

def has_bad_words(original, result, words):
    return any(word in original != word in result for word in words)

def get_query(title, artist):
    artist = " ".join(filter(
        lambda word: "feat" not in word
        and word not in string.punctuation and len(word) > 1,
        artist.lower().split()))

    return remove_parens(title) + " " + " ".join(artist.split()[:3])

def search_item(item_type, title, artist):
    title_bb = title.lower().strip()
    artist_bb = artist.lower().strip() if artist else ""
    query = get_query(title_bb, artist_bb)
    search_results = Spotify().search(q=query, type=item_type, limit=50)

    failed = []
    for result in search_results[item_type + "s"]["items"]:
        item = remove_parens(result["name"].lower())
        if has_bad_words(title_bb, item, ["cover", "karaoke", "remix"]):
            continue

        artist_spoffy = result["artists"][0]["name"].lower()
        if has_bad_words(artist_bb, artist_spoffy, ["tribute", "karaoke"]):
            break

        if (LSSMatch(artist_bb, artist_spoffy) >= .75 or artist_bb == "soundtrack") \
            and LSSMatch(item, title_bb) >= .75:
            return SpotifyItem(item_type, title, artist, search=search_result)

        failed.append("\"%s\" by %s" % (item, result["artists"][0]["name"]))

    print("\"%s\" not found" % (query))
    for fail in failed[:5]:
        print("\t", fail)

    return SpotifyItem(item_type, title, artist)


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


def sql_prep(s):
    return "\"%s\"" % MySQLdb.escape_string(s) if isinstance(s, str) \
           else MySQLdb.escape_string(str(s))

INFO = {
    "hot-100": {
        "chart": "hot-100",
        "url": lambda x: "https://www.billboard.com/charts/hot-100/" + x,
        "item_type": "track",
    },

    "billboard-200": {
        "chart": "billboard-200",
        "url": lambda x: "https://www.billboard.com/charts/billboard-200/" + x,
        "item_type": "album",
    }
}


class SpotifyItem:
    def __init__(self, item_type, title, artist, search_result=None, uri=None):
        self.type = item_type
        self.details = {
            "bb_artist": artist,
            "bb_title": title
        }

        if uri:
            uri_object = Spotify().album(uri) if type=="album" else Spotify().track(uri)
        elif search_result:
            uri_object = search_result
            if item_type == "track":
                self.album_uri = search_result["album"]["uri"]
                self.album_type = search_result["album"]["album_type"]
        else:
            return

        self.details.update({
            "uri": uri if uri else uri_object["uri"],
            "spoffy_artist": ",".join(x["name"] for x in uri_object["artists"]),
            "spoffy_title": uri_object["name"],
            "popularity": uri_object["popularity"],
            "duration": sum(uri_object["duration_ms"] for track
                            in uri_object["tracks"]["items"]) if item_type == "album" \
                        else uri_object["duration_ms"],
            "genres": ",".join(uri_object["genres"])
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

if __name__ == "__main__":
    scrape()
