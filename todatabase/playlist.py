from bs4 import BeautifulSoup
import math
import os
import pprint
import requests
import spotipy
import spotipy.util as util
import sys
import urllib

import MySQLdb
conn = MySQLdb.connect(host= "localhost",
                  user="root",
                  passwd=os.environ["MYSQL_PASSWORD"],
                  db="billboard")
cur = conn.cursor()

def main(year, replace=True):
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user) #TODO: Error uncaught

    cur.execute("SELECT uri FROM ( \
        SELECT distinct songid as id, song, artist, popularity FROM billboard.topsongs join songs on (songid = id) where year(week) = 2000 group by songid) o \
        JOIN uris using (id) where uri is not null  order by popularity desc")

    uris = []
    for r in cur:
        uris.append(r[0])

    if replace:
        replace_playlist(sp, user, "BB", year, uris)
    else:
        make_playlist(sp, user, "BB", year, uris)

def get_token(user):
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(user, scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def replace_playlist(sp, user, prefix, year, uris, partitions=12):
    all_playlists = sp.user_playlists(user)["items"]
    relevant_playlists = []
    offset_now = 50
    while len(all_playlists) > 0:
        relevant_playlists += [playlist for playlist in all_playlists \
            if playlist["name"].startswith(prefix + "-")]
        all_playlists = sp.user_playlists(user, offset=offset_now)["items"]
        offset_now += 50

    if not relevant_playlists:
        make_playlist(sp, user, prefix, year, songs, partitions)
    else:
        if len(relevant_playlists) != partitions:
            raise IOError("Unexpected number of playlists: " + str(len(relevant_playlists)))

        relevant_playlists.sort(key = lambda x : int(x["name"].split(":")[0][3:]))
        playlist_len = int(math.ceil(len(uris) / float(partitions)))

        for idx, playlist in enumerate(relevant_playlists):
            start = idx*playlist_len
            sp.user_playlist_replace_tracks(user, playlist["id"], uris[start:start+playlist_len])

            oldname = playlist["name"]
            newname = oldname.split(":")[0] + ": " + year
            rename_playlist(sp, user, playlist["id"], newname)

def make_playlist(sp, user, prefix, year, uris, partitions=12):
    playlist_len = int(math.ceil(len(uris) / float(partitions)))
    for i in range(0, len(uris), playlist_len):
        idx = i/playlist_len + 1
        playlist = sp.user_playlist_create(user, "{}-{}: {}".format(prefix, idx, year))
        playlist_id = playlist["id"]
        sp.user_playlist_add_tracks(user, playlist_id, uris[i:i+playlist_len])

    print len(uris), "songs added"

def delete_playlist(sp, user, playlist):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}/followers" \
        .format(user, playlist)
    response = sp._delete(rest)

def rename_playlist(sp, user, playlist, new_name):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}" \
        .format(user, playlist)
    data = {
        "name": new_name
    }

    response = sp._put(rest, payload=data)

if __name__ == "__main__":
    years = sys.argv[1]
    main(years)#True)
