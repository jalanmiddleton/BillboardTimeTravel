import os
from random import shuffle
import spotipy
import spotipy.util as util
import sys

def main():
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user)
    playlistid, playlist = findplaylist(sp, user, "Quizzable")
    details = [x["track"] for x in playlist["tracks"]["items"]]
    tracks = [{ 'name': x['name'], 'artist': x['artists'][0]['name'], 'uri': x['uri'] } for x in details]
    shuffle(tracks)

    sp._put("https://api.spotify.com/v1/me/player/play", payload={
            'uris': [x['uri'] for x in tracks]
    })

    while True:
        song = raw_input("Song? ")
        artist = raw_input("Artist? ")

        current = sp._get("https://api.spotify.com/v1/me/player/currently-playing")
        realartist = current["item"]["artists"][0]["name"]
        realsong = current["item"]["name"]
        if artist.lower() == realartist.lower() and realsong.lower().startswith(song.lower()):
            remove = raw_input("Nice! Remove? (y/n) ")
            if remove == "y":
                sp.user_playlist_remove_all_occurrences_of_tracks(user, playlistid, [current["item"]["uri"]])

            skip = raw_input("Skip? (y/n) ")
            if skip == "y":
                sp._post("https://api.spotify.com/v1/me/player/next")
        else:
            print "booo, it was %s by %s" % (realsong, realartist)
        print

def get_token(user):
    scope = 'streaming,user-read-currently-playing,playlist-modify-public'
    token = util.prompt_for_user_token(user, scope=scope, \
        client_id=os.environ["SPOTIPY_CLIENT_ID"], \
        client_secret=os.environ["SPOTIPY_CLIENT_SECRET"])
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def getplaylistbynum(sp, user, num):
    playlistname = "BB-" + num + ":"
    return findplaylist(sp, user, playlistname)

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

if __name__ == "__main__":
    #command = sys.argv[1]
    main()
