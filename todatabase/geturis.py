from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import math
import os
import pprint
import requests
import spotipy
import spotipy.util as util
import string
from nltk.corpus import stopwords
import sys
import urllib

import MySQLdb
conn = MySQLdb.connect(host= "localhost",
                  user="root",
                  passwd=os.environ["MYSQL_PASSWORD"],
                  db="billboard")
cur = conn.cursor()
updatecur = conn.cursor()


#TODO: I don't want default to be all years.
def main():
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user) #TODO: Error uncaught

    cur.execute("SELECT * FROM songs where id > 0;")
    for id, song, artist in cur:
        while True:
            try:
                uri = get_song_link(sp, song, artist)
                if uri is not None:
                    q = "UPDATE billboard.uris SET uri='{}', song='{}', artist='{}' WHERE id={}".format(uri["uri"], uri["song"], uri["artist"], id)
                    updatecur.execute(q)
                    conn.commit()
                break
            except Exception as e:
                print e
                sp = get_token(user)

def get_token(user):
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(user, scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def get_song_link(sp, title, artist):
    title = "".join([l if l not in string.punctuation else "" if l == "'" else " " for l in title.lower().strip()])
    #artist = "".join([l for l in artist.lower().strip() if l not in string.punctuation])
    artist = " ".join([w for w in artist.lower().split() if w != "featuring"])

    #title = " ".join([word for word in title.split() if word not in stopwords.words('english')])
    #artist = " ".join([word for word in artist.split() if word not in stopwords.words('english')])

    query = title \
        + " " \
        + "artist:" + " ".join( artist.split()[:3] )
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
                "artist": artist_result["name"].replace("'", "").replace("\\", "\\\\").encode('utf-8'), \
                "song": result["name"].replace("'", "").replace("\\", "\\\\").encode('utf-8') }

    return None

def LSSMatch(one, two):
    shortest = one if len(one) < len(two) else two
    longest = one if shortest == two else two

    if len(shortest) == 0:
        return 0

    matrix = [[0 for i in range(len(shortest) + 1)] for j in range(len(longest) + 1)]
    for x in range(1, len(longest) + 1):
        for y in range(1, len(shortest) + 1):
            matrix[x][y] = (matrix[x-1][y-1] + 1) if longest[x-1] == shortest[y-1] else max(matrix[x-1][y], matrix[x][y-1])

    return float(matrix[-1][-1]) / len(shortest)

if __name__ == "__main__":
    main()
