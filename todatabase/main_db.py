from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import math
import os
import pprint
import requests
import sys
import urllib

import MySQLdb
conn = MySQLdb.connect(host= "localhost",
                  user="root",
                  passwd=os.environ["MYSQL_PASSWORD"],
                  db="billboard")
cur = conn.cursor()

#15Aug16 API doesn't support delete!!!!!!

#TODO: I don't want default to be all years.
def main(years=range(1955, 2018), replace=False, debug=False):
    day = datetime(1961, 1, 17)# datetime(2017, 12, 30)
    delta = timedelta(7)
    while day.year > 1957:
        try:
            songs = get_songs_from_page(day)
            addsongs(songs)
        except Exception as e:
            print e
            continue

        day = day - delta

def get_songs_from_page(day):
    print day
    page = "https://www.billboard.com/charts/hot-100/{}-{}-{}" \
        .format(day.year, \
            day.month if day.month >= 10 else "0"+str(day.month), \
            day.day if day.day >= 10 else "0"+str(day.day))
    print page
    page_html = urllib.urlopen(page)
    page_soup = BeautifulSoup(page_html, "html.parser")
    chart_rows = page_soup.find_all("div", "chart-row__main-display")

    songs = []
    for row in chart_rows:
        song_artist_spotify = extract_song_info(row)
        song_artist_spotify["day"] = day
        songs.append(song_artist_spotify)

    print songs
    return songs

def extract_song_info(row):
    title = row.find(class_ = "chart-row__song").getText().strip()
    artist = row.find(class_ = "chart-row__artist").getText().strip()
    spotify_button = row.find(class_ = "js-spotify-play-full")

    spotify = None
    if (spotify_button is not None):
        spotify = spotify_button["data-href"]

    return { "title":title, "artist":artist, "spotify":spotify, "score":0 }

def addsongs(songs):
    querysongs = []
    for i, x in enumerate(songs):
        querysongs.append("('{}', {}, '{}', '{}')" \
            .format("{}-{}-{}".format(x["day"].year, \
                x["day"].month if + x["day"].month >= 10 else "0"+str(x["day"].month), \
                x["day"].day if x["day"].day >= 10 else "0"+str(x["day"].day)), \
            i+1, x["title"].replace("'", "\\'").encode('utf-8'), x["artist"].replace("'", "\\'").encode('utf-8')))
    values = reduce(lambda a, b: a + "," + b, querysongs)
    cur.execute("INSERT INTO billboard.topsongs (week, idx, song, artist) VALUES " + values)
    conn.commit()

if __name__ == "__main__":
    main()
