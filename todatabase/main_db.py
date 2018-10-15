from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import math
import os
import pprint
import requests
import spotipy
import spotipy.oauth2
import spotipy.util as util
import string
import sys
import urllib2

import MySQLdb
conn = MySQLdb.connect(host= "localhost", user="root", \
                  passwd=os.environ["MYSQL_PASSWORD"], db="billboard")
cur = conn.cursor()

def main(years=range(1955, 2018), replace=False, debug=False):
    day = datetime(2018, 10, 13)
    while day.year > 1957:
        try:
            songs = get_songs_from_page(day)
        except Exception as e:
            print str(e)
            continue #try again

        addsongs(songs, day)
        day -= timedelta(7)

def get_songs_from_page(day):
    print day
    page = "https://www.billboard.com/charts/hot-100/{}-{}-{}" \
        .format(day.year, \
            day.month if day.month >= 10 else "0"+str(day.month), \
            day.day if day.day >= 10 else "0"+str(day.day))
    page_soup = BeautifulSoup(urllib2.urlopen(urllib2.Request(page, \
        headers={ 'User-Agent' : 'Mozilla/5.0' })), "html.parser")
    return extract_song_info(page_soup)

html_to_dict = lambda html : {"title": html[0].getText().strip().replace("\'", "\\\'s"), \
    "artist": html[1].getText().strip().replace("\'", "\\\'s")}
def extract_song_info(page):
    songs = [html_to_dict(page.find(class_="chart-number-one__details").find_all("div"))]
    for song in [song.find_all("div") for song in page.find_all(class_="chart-list-item__text")]:
        songs.append(html_to_dict(song))
    return songs

def addsongs(songs, day):
    sp = get_token()
    querysongs = []
    for i, x in enumerate(songs):
        select = "SELECT id from songs where song = '%s' and artist = '%s'" % (x["title"], x["artist"])
        cur.execute(select)
        idres = cur.fetchall()

        if not idres:
            uri = get_song_link(sp, x["title"], x["artist"])
            cur.execute("INSERT IGNORE INTO billboard.songs (song, artist, popularity) \
                VALUES ('%s', '%s', %s)" % (x["title"], x["artist"], uri["popularity"] if uri else "null"))
            conn.commit()
            cur.execute(select)
            idres = cur.fetchall()

            if uri:
                try:
                    cur.execute("INSERT IGNORE INTO billboard.uris (id, uri, song, artist) VALUES (%s, '%s', '%s', '%s')" % (idres[0][0], uri["uri"], uri["title"], uri["artist"]))
                    conn.commit()
                except Exception as e:
                    print uri

        id = idres[0][0]
        week = "{}-{}-{}".format(day.year, \
            day.month if + day.month >= 10 else "0"+str(day.month), \
            day.day if day.day >= 10 else "0"+str(day.day))
        cur.execute("INSERT IGNORE INTO billboard.weeks (week, idx, songid) VALUES ('%s', %s, %s)" \
            % (week, i+1, id))
        conn.commit()

def get_token():
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(os.environ['SPOTIFY_USER'], scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def get_song_link(sp, title, artist):
    while True:
        try:
            title = "".join([l if l not in string.punctuation else "" if l == "'" else " " for l in title.lower().strip()])
            artist = " ".join([w for w in artist.lower().split() if w != "featuring"])

            query = title + " artist:" + " ".join( artist.split()[:3] )
            search_results = sp.search(q=query, type="track", limit=50)

            for result in search_results["tracks"]["items"]:
                track = result["name"].lower()
                if ("cover" not in title and "cover" in track) or \
                    ("karaoke" not in title and "karaoke" in track) or \
                    ("remix" not in title and "remix" in track):
                    continue

                for artist_result in result["artists"]:
                    artist_lower = artist.strip().lower()
                    artist_result_lower = artist_result["name"].strip().lower()

                    if "tribute" in artist_result_lower or "karaoke" in artist_result_lower:
                        continue

                    if LSSMatch(artist, artist_result_lower)  >= .75 and LSSMatch(track, title) >= .75:
                        return { "uri": result["uri"], \
                        "artist": artist_result["name"].replace("'", "").replace("\\", "\\\\").encode("utf-8"), \
                        "title": result["name"].replace("'", "").replace("\\", "\\\\").encode("utf-8"),
                        "popularity": result["popularity"] }

            break
        except Exception as e:
            print e
            sp = get_token()

    return None

def LSSMatch(one, two):
    shortest = one if len(one) < len(two) else two
    longest = one if shortest == two else two

    if len(shortest) == 0:
        return 0

    matrix = [[0 for i in range(len(shortest) + 1)] for j in range(len(longest) + 1)]
    for x in range(1, len(longest) + 1):
        for y in range(1, len(shortest) + 1):
            matrix[x][y] = (matrix[x-1][y-1] + 1) if longest[x-1] == shortest[y-1] \
                else max(matrix[x-1][y], matrix[x][y-1])

    return float(matrix[-1][-1]) / len(shortest)

if __name__ == "__main__":
    main()
