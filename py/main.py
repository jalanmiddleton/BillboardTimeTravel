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
from bs4 import BeautifulSoup

from core import _conn, _cur, InitDB, Spotify


def replace_playlist(id, newname, tracks):
    Spotify().user_playlist_replace_tracks(
        secrets['SPOTIFY_USER'], id, tracks)
    rename_playlist(secrets['SPOTIFY_USER'], id, newname)


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


def scramble():
    def pop(playlist):
        if playlist["name"] in ["POP-START", "POP-END"]:
            pop.between = not pop.between
            return False
        else:
            return pop.between
    pop.between = False

    playlists = findplaylists(Spotify(), secrets['SPOTIFY_USER'], pop)
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

if __name__ == "__main__":
    scramble()
