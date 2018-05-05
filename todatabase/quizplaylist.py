import os
from random import shuffle
import spotipy
import spotipy.util as util
import sys

def main(num):
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user)
    playlist = getplaylist(sp, user, num)
    details = [x["track"] for x in playlist["tracks"]["items"]]
    tracks = [{ 'name': x['name'], 'artist': x['artists'][0]['name'], 'uri': x['uri'] } for x in details]
    shuffle(tracks)

    sp._put("https://api.spotify.com/v1/me/player/play", payload={
            'uris': [x['uri'] for x in tracks]
    })

    print dir(sp)
    while True:
        raw_input()
        sp._post("https://api.spotify.com/v1/me/player/next")

def get_token(user):
    scope = 'streaming'
    token = util.prompt_for_user_token(user, scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def getplaylist(sp, user, num):
    all_playlists = sp.user_playlists(user)["items"]
    offset_now = 50
    playlistname = "BB-" + num + ":"

    while len(all_playlists) > 0:
        for playlist in all_playlists:
            if playlist["name"].startswith(playlistname):
                return sp.user_playlist(user, playlist["id"], fields="tracks,next")
        all_playlists = sp.user_playlists(user, offset=offset_now)["items"]
        offset_now += 50

    return None

if __name__ == "__main__":
    num = sys.argv[1]
    main(num)
