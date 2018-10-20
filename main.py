import math
import os
import pprint
import re
import string
import sys
import urllib2
from datetime import datetime, timedelta

import MySQLdb
import requests
import spotipy
import spotipy.oauth2
import spotipy.util as util
from bs4 import BeautifulSoup

conn = MySQLdb.connect(host="localhost", user="root",
                       passwd=os.environ["HOST_PASSWORD"], db="billboard")
cur = conn.cursor()


_sp = None


def spotify():
    try:
        _sp.me()
    except Exception as e:
        token = util.prompt_for_user_token(
            os.environ['SPOTIFY_USER'], 'playlist-modify-public')
        _sp = spotipy.Spotify(auth=token)
    finally:
        return _sp


def scrape_bb(day=datetime(2018, 10, 13), years=range(1955, 2018)):
    while day.year > 1957:
        songs = get_from_page(day)
        add_songs(songs, day)
        day -= timedelta(7)
        break


def get_from_page(day, get_tracks=True):
    print day

    day_url = ("https://www.billboard.com/charts/hot-100/{}-{}-{}" if get_tracks
               else "https://www.billboard.com/charts/billboard-200/{}-{}-{}") \
        .format(day.year, format(day.month, '02'), format(day.day, '02'))
    raw_html = urllib2.urlopen(urllib2.Request(
        day_url, headers={'User-Agent': 'Mozilla/5.0'}))
    page_soup = BeautifulSoup(raw_html, "html.parser")

    return extract_song_info(page_soup)


# Expect all chart items to have two and only two internal divs.
def html_to_dict(html): return {
    "title": html[0].getText().strip().replace("\'", "\\\'").encode("utf8"),
    "artist": html[1].getText().strip().replace("\'", "\\\'").encode("utf8")
}


def extract_song_info(page):
    # The number one spot is in a format of its own, so extract as a single item.
    songs = [html_to_dict(page.find(class_="chart-number-one__details")
                          .find_all("div"))]

    for song in [song.find_all("div")
                 for song in page.find_all(class_="chart-list-item__text")]:
        songs.append(html_to_dict(song))
    return songs


def add_songs(songs, day):
    for i, song in enumerate(songs):
        select = "SELECT id from songs where song = '%s' and artist = '%s'" \
            % (song["title"], song["artist"])

        cur.execute(select)
        idres = cur.fetchall()

        if not idres:
            uri = get_song_link(song["title"], song["artist"])
            cur.execute("INSERT IGNORE INTO billboard.songs (song, artist, popularity) \
                VALUES ('%s', '%s', %s)" % (song["title"], song["artist"],
                                            uri["popularity"] if uri else "null"))

            cur.execute(select)
            idres = cur.fetchall()

            if uri:
                insert_uri = "INSERT IGNORE INTO billboard.uris (id, uri, song, artist) VALUES (%s, '%s', '%s', '%s')" \
                    % (idres[0][0], uri["uri"], uri["title"], uri["artist"])
                cur.execute(insert_uri)

        id = idres[0][0]
        week = "{}-{}-{}".format(day.year, day.month if + day.month >= 10 else "0"
                                 + str(day.month), format(day.day, "02"))
        cur.execute("INSERT IGNORE INTO billboard.weeks (week, idx, songid) VALUES ('%s', %s, %s)"
                    % (week, i + 1, id))
        conn.commit()


def get_song_link(title, artist):
    title = "".join([l if l not in string.punctuation else "'" if l == "'"
                     else "*" if l == "*" else " " for l in title.lower().strip()])
    title = " ".join([l for l in title.split() if "*" not in l])
    artist = " ".join(
        [w for w in artist.lower().split() if w != "featuring" and w != "&"])

    query = title + " artist:" + " ".join(artist.split()[:2])
    search_results = spotify().search(q=query, type="track", limit=50)

    print query
    for result in search_results["tracks"]["items"]:
        track = result["name"].lower().encode("utf-8")
        if ("cover" not in title and "cover" in track) or \
            ("karaoke" not in title and "karaoke" in track) or \
                ("remix" not in title and "remix" in track):
            continue

        for artist_result in result["artists"]:
            artist_lower = artist.strip().lower().encode("utf-8")
            artist_result_lower = artist_result["name"].strip(
            ).lower().encode("utf-8")

            if "tribute" in artist_result_lower or "karaoke" in artist_result_lower:
                continue

            print artist, artist_result_lower, LSSMatch(
                artist, artist_result_lower)
            print track, title, LSSMatch(track, title)
            print
            if LSSMatch(artist, artist_result_lower) >= .75 and LSSMatch(track, title) >= .75:
                return {"uri": result["uri"],
                        "artist": artist_result["name"].encode("utf8"),
                        "title": result["name"].encode("utf8"),
                        "popularity": result["popularity"]}

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

################################################################################


def fill_in_uris():
    cur.execute("SELECT * FROM songs where id not in (SELECT id FROM uris)")
    for song in cur.fetchall():
        print song
        songname = re.sub(r"'s(\w)", r"'\1", song[1])
        uri = get_song_link(songname, song[2])

        if uri:
            newuri = ("INSERT IGNORE INTO billboard.uris (id, uri, song, artist) VALUES (%s, '%s', '%s', '%s')"
                      % (song[0], uri["uri"], uri["title"].decode("utf8"), uri["artist"].decode("utf8"))).encode("utf8")
            cur.execute(newuri)
            cur.execute("UPDATE billboard.songs SET song='%s', popularity = %s where id = %s"
                        % (songname.replace("'", "\\'"), uri["popularity"], song[0]))
            conn.commit()

################################################################################


def replace_playlist(user, prefix, uris, newname, partitions=6):
    all_playlists = spotify().user_playlists(user)["items"]
    relevant_playlists = []
    offset_now = 50
    while len(all_playlists) > 0:
        relevant_playlists += [playlist for playlist in all_playlists
                               if playlist["name"].startswith(prefix + ":")]
        all_playlists = spotify().user_playlists(
            user, offset=offset_now)["items"]
        offset_now += 50

    if len(relevant_playlists) < partitions:
        raise IOError("Unexpected number of playlists: "
                      + str(len(relevant_playlists)))
    else:
        relevant_playlists = relevant_playlists[:partitions]

    relevant_playlists.sort(key=lambda x: x["name"])
    playlist_len = int(math.ceil(len(uris) / float(partitions)))

    for idx, playlist in enumerate(relevant_playlists):
        start = idx * playlist_len
        spotify().user_playlist_replace_tracks(
            user, playlist["id"], uris[start:start + playlist_len])
        rename_playlist(user, playlist["id"], "BB: " + newname)


def rename_playlist(user, playlist, new_name):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}" \
        .format(user, playlist)
    data = {
        "name": new_name
    }

    response = spotify()._put(rest, payload=data)


def delete_playlist(sp, user, playlist):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}/followers" \
        .format(user, playlist)
    response = sp._delete(rest)

################################################################################


def findplaylist(sp, user, name):
    all_playlists = sp.user_playlists(user)["items"]
    offset_now = 50
    while len(all_playlists) > 0:
        for playlist in all_playlists:
            if playlist["name"].startswith(name):
                return playlist["id"], sp.user_playlist(user, playlist["id"], fields="tracks,next")
        all_playlists = sp.user_playlists(user, offset=offset_now)["items"]
        offset_now += 50

    return None


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
    scrape_bb()
    # fill_in_uris()
    #cur.execute("select distinct uri from weeks join uris on (songid = id) join songs using (id) where idx <= 3 and week between '2000-01-01' and '2006-01-01' order by popularity desc")
    # replace_playlist(get_token(), os.environ['SPOTIFY_USER'], "BB", [
    #                 x[0] for x in cur.fetchall()], "1-3s from Early Aughts")
