import math
import os
import pprint
import re
import string
import sys
import urllib2
from datetime import datetime, timedelta
from random import shuffle

import MySQLdb
import requests
import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
from bs4 import BeautifulSoup

conn = MySQLdb.connect(host="localhost", user="root",
                       passwd=os.environ["HOST_PASSWORD"], db="billboard",
                       use_unicode=True, charset="utf8")
cur = conn.cursor()


_token = None
_sp = None
_credentials = oauth2.SpotifyClientCredentials()


def Spotify():
    if not _token or _credentials.is_token_expired(_token):
        token = util.prompt_for_user_token(
            os.environ['SPOTIFY_USER'], 'playlist-modify-public')
        _sp = spotipy.Spotify(
            auth=token, client_credentials_manager=_credentials)

    return _sp


INFO = {
    "hot-100": {
        "chart": "hot-100",
        "url": "https://www.billboard.com/charts/hot-100/{}-{}-{}",
        "item_type": "track",
        "popularity": lambda result: result["popularity"]
    },
    "billboard-200": {
        "chart": "billboard-200",
        "url": "https://www.billboard.com/charts/billboard-200/{}-{}-{}",
        "item_type": "album",
        "popularity": lambda result: Spotify().album(result["uri"])["popularity"]
    }
}


def scrape(day=datetime(2018, 11, 3), end_year=1957):
    while day.year > end_year:
        try:
            add_items(get_from_page(
                INFO["hot-100"], day), day, INFO["hot-100"])
            add_items(get_from_page(
                INFO["billboard-200"], day), day, INFO["billboard-200"])
            day -= timedelta(7)
        except Exception as e:
            print e
            continue


def get_from_page(info, day):
    print day

    day_url = info["url"].format(day.year, format(
        day.month, '02'), format(day.day, '02'))
    raw_html = urllib2.urlopen(urllib2.Request(
        day_url, headers={'User-Agent': 'Mozilla/5.0'}))
    page_soup = BeautifulSoup(raw_html, "html.parser")

    return extract_item_info(page_soup)


def sql_prep(str): return unicode(
    str.strip().replace("\\", "").replace("\'", "\\\'").encode("utf8"), "utf8")


def extract_item_info(page):
    def html_to_dict(html): return {
        "title": html[0].getText(),
        "artist": html[1].getText()
    }

    # The number one spot is in a format of its own, so extract as a single item.
    items = [html_to_dict(page.find(class_="chart-number-one__details")
                          .find_all("div"))]

    for item in [item.find_all("div")
                 for item in page.find_all(class_="chart-list-item__text")]:
        items.append(html_to_dict(item))
    return items


def add_items(items, day, info):
    for i, item in enumerate(items):
        select = "SELECT id from %ss where title = '%s' and artist = '%s'" \
            % (info["item_type"], sql_prep(item["title"]), sql_prep(item["artist"]))
        cur.execute(select)
        idres = cur.fetchall()

        if not idres:
            uri = get_item_link(item["title"], item["artist"], info)

            cur.execute("INSERT IGNORE INTO %ss (title, artist, uri, popularity, \
                spoffy_title, spoffy_artist) VALUES ('%s', '%s', %s, %s, %s, %s)"
                        % (info["item_type"],
                           sql_prep(item["title"]), sql_prep(item["artist"]),
                            "'%s'" % (uri["uri"]) if uri else "NULL",
                           uri["popularity"] if uri else "NULL",
                           "'%s'" % (sql_prep(uri["title"])
                                     ) if uri else "NULL",
                           "'%s'" % (sql_prep(uri["artist"])) if uri else "NULL"))

            cur.execute(select)
            idres = cur.fetchall()

        id = idres[0][0]
        week = "{}-{}-{}".format(day.year,
                                 format(day.month, "02"), format(day.day, "02"))
        cur.execute("INSERT IGNORE INTO billboard.`%s` (week, idx, item_id) VALUES ('%s', %s, %s)"
                    % (info["chart"], week, i + 1, id))
        conn.commit()


def get_item_link(title, artist, info):
    title = title.lower().strip()
    artist = " ".join(filter(
        lambda word: "feat" not in word \
            and word not in string.punctuation and len(word) > 1,
        artist.lower().split()))

    query = re.sub(r"\(.+\)|[.+]", "", title) + \
        " " + " ".join(artist.split()[:2])
    search_results = Spotify().search(
        q=query, type=info["item_type"], limit=50)

    failed = []
    for result in search_results[info["item_type"] + "s"]["items"]:
        item = re.sub(r"\(.+\)|[.+]", "", result["name"].lower())
        if ("cover" not in title and "cover" in item) or \
            ("karaoke" not in title and "karaoke" in item) or \
                ("remix" not in title and "remix" in item):
            continue

        for artist_result in result["artists"]:
            artist_lower = artist_result["name"].lower()
            if "tribute" in artist_lower or "karaoke" in artist_lower:
                continue

            if (LSSMatch(artist, artist_lower) >= .75 or artist == "soundtrack") and LSSMatch(item, title) >= .75:
                return {"uri": result["uri"],
                        "artist": artist_result["name"],
                        "title": result["name"],
                        "popularity": info["popularity"](result)}
        failed.append("\"%s\" by %s" % (item, result["artists"][0]["name"]))

    print "\"%s\" not found" % (query.encode("utf8"))
    for fail in failed[:5]:
        print "\t", fail.encode("utf8")

    return None


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
    global cur
    cur.execute(
        "truncate albums; truncate `billboard-200`; truncate `hot-100`; truncate tracks;")
    cur.close()
    cur = conn.cursor()
################################################################################


def fill_in_uris():
    cur.execute("SELECT * FROM songs where id not in (SELECT id FROM uris)")
    for song in cur.fetchall():
        print song

        uri = get_song_link(song[1], song[2])
        if uri:
            newuri = "INSERT IGNORE INTO billboard.uris (id, uri, song, artist) VALUES (%s, '%s', '%s', '%s')" \
                % (song[0], uri["uri"], sql_prep(uri["title"]), sql_prep(uri["artist"]))
            cur.execute(newuri)
            cur.execute("UPDATE billboard.songs SET song='%s', popularity = %s where id = %s"
                        % (song[1].replace("'", "\\'"), uri["popularity"], song[0]))
            conn.commit()


################################################################################


def replace_playlist(id, newname, tracks):
    Spotify().user_playlist_replace_tracks(
        os.environ['SPOTIFY_USER'], id, tracks)
    rename_playlist(os.environ['SPOTIFY_USER'], id, newname)


def rename_playlist(user, playlist, new_name):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}" \
        .format(user, playlist)
    data = {
        "name": new_name
    }

    response = Spotify()._put(rest, payload=data)


def delete_playlist(sp, user, playlist):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}/followers" \
        .format(user, playlist)
    response = sp._delete(rest)


################################################################################


def scramble():
    def pop(playlist):
        if playlist["name"] in ["POP-START", "POP-END"]:
            pop.between = not pop.between
            return False
        else:
            return pop.between
    pop.between = False

    playlists = findplaylists(Spotify(), os.environ['SPOTIFY_USER'], pop)
    ids, tracks = [p[0] for p in playlists], [(p[1], [u["track"]["uri"] for u in p[2]["tracks"]["items"]]) for p in playlists]
    shuffle(tracks)

    for id, track in zip(ids, tracks):
        replace_playlist(id, track[0], track[1])

def findplaylists(sp, user, filt):
    all_playlists = sp.user_playlists(user)["items"]
    offset_now = 50
    results = []

    while len(all_playlists) > 0:
        for playlist in all_playlists:
            if filt(playlist):
                results.append((playlist["id"], playlist["name"], sp.user_playlist(user, playlist["id"], fields="tracks,next")))

        all_playlists = sp.user_playlists(user, offset=offset_now)["items"]
        offset_now += 50

    return results


################################################################################


def quiz():
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user)
    playlistid, playlist = findplaylist(sp, user, "Quizzable")
    details = [x["track"] for x in playlist["tracks"]["items"]]
    tracks = [{'name': x['name'], 'artist': x['artists']
               [0]['name'], 'uri': x['uri']} for x in details]
    shuffle(tracks)

    sp._put("https://api.spotify.com/v1/me/player/play", payload={
            'uris': [x['uri'] for x in tracks]
            })

    while True:
        song = raw_input("Song? ")
        artist = raw_input("Artist? ")

        current = sp._get(
            "https://api.spotify.com/v1/me/player/currently-playing")
        realartist = current["item"]["artists"][0]["name"]
        realsong = current["item"]["name"]
        if artist.lower() == realartist.lower() and realsong.lower().startswith(song.lower()):
            remove = raw_input("Nice! Remove? (y/n) ")
            if remove == "y":
                sp.user_playlist_remove_all_occurrences_of_tracks(
                    user, playlistid, [current["item"]["uri"]])

            skip = raw_input("Skip? (y/n) ")
            if skip == "y":
                sp._post("https://api.spotify.com/v1/me/player/next")
        else:
            print "booo, it was %s by %s" % (realsong, realartist)
        print


if __name__ == "__main__":
    scramble()

    # truncate_all()
    # scrape()
    # fill_in_uris()
    #cur.execute("select distinct uri from weeks join uris on (songid = id) join songs using (id) where idx <= 3 and week between '2000-01-01' and '2006-01-01' order by popularity desc")
    # replace_playlist(get_token(), os.environ['SPOTIFY_USER'], "BB", [
    #                 x[0] for x in cur.fetchall()], "1-3s from Early Aughts")
