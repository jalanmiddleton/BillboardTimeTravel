'''
This script used the independent website http://www.spotifynewmusic.com/ to find a selection of 
new albums every week. This website no longer exists! This script is therefore obsolete.
'''

from bs4 import BeautifulSoup
from urllib.request import urlopen
import spotipy
import spotipy.util as util
import os
from secrets import secrets

def get_token(user):
    # Scopes listed here: https://developer.spotify.com/documentation/general/guides/scopes/
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(user, scope,
                            client_id=secrets["SPOTIPY_CLIENT_ID"],
                            client_secret=secrets["SPOTIPY_SECRET"],
                            redirect_uri=secrets["SPOTIPY_REDIRECT_URI"])
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def find_playlist(sp, user):
    all_playlists = sp.user_playlists(user)["items"]
    relevant_playlists = []
    offset_now = 50
    while len(all_playlists) > 0:
        for playlist in all_playlists:
            print(playlist["name"])
            if playlist["name"] == "Weekly New Albums":
                return playlist
        all_playlists = sp.user_playlists(user, offset=offset_now)["items"]
        offset_now += 50

    return None

page_html = urlopen("http://www.spotifynewmusic.com/")
page_soup = BeautifulSoup(page_html, "html.parser")
play_links = page_soup.find_all("div", "play")
user = secrets['SPOTIFY_USER']
sp = get_token(user) #TODO: Error uncaught
playlist = find_playlist(sp, user)["uri"]
all_songs = []
for link in play_links:
    try:
        album_link = link.find("a").get("href")
        tracks = sp.album_tracks(album_link)
        all_songs += [x["uri"] for x in tracks["items"][:3]]
    except Exception as e:
        print(str(e))
sp.user_playlist_replace_tracks(user, playlist, [])
for i in range(0, len(all_songs), 100):
    sp.user_playlist_add_tracks(user, playlist, all_songs[i:i+100])
