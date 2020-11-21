from core import Spotify
from secrets import secrets
from random import shuffle

'''
Return the playlists between the flags.
'''
def flag_filter(flag_start="POP-START", flag_end="POP-END"):
    def my_filter(playlist):
        if playlist["name"] in [flag_start, flag_end]:
            my_filter.between = not my_filter.between
            return False
        else:
            return my_filter.between
    my_filter.between = False
    return my_filter

'''
Randomly reorder a set of Spotify playlists on my account.
The set is identified by two flags---empty playlists by a certain name---before
  and after the playlists I want.
'''


def scramble():
    playlists = filter_playlists(secrets['SPOTIFY_USER'], flag_filter())
    ids = [p.id for p in playlists]
    shuffle(playlists)

    for id, album in zip(ids, playlists):
        Spotify().user_playlist_replace_tracks(
            secrets['SPOTIFY_USER'], id, album.tracks)
        Spotify().user_playlist_change_details(
            secrets['SPOTIFY_USER'], id, album.name)


class Playlist:
    def __init__(self, user, partial_playlist):
        playlist = Spotify().user_playlist(user, partial_playlist["id"],
                                           fields="id,name,tracks,uri,next")

        self.id = playlist['id']
        self.name = playlist['name']
        self.tracks = [t['track']['uri'] for t in playlist['tracks']['items']]
        self.uri = playlist['uri']




'''
Returns the set of personal playlists as identified by a passed-in filter.
The order by which playlists are processed is assumed to be the top-to-bottom
  order as is on the Spotify interface.

sp: The Spotipy object
user: The Spotify user id.
filt: A function that returns true or false for whether the playlist qualifies.
'''


def filter_playlists(user, filt):
    all_playlists = Spotify().current_user_playlists()["items"]
    offset_now = 50
    results = []

    while len(all_playlists) > 0:
        results.extend(Playlist(user, p) for p in all_playlists if filt(p))
        all_playlists = Spotify().current_user_playlists(offset=offset_now)["items"]
        offset_now += 50

    return results


if __name__ == "__main__":
    scramble()
