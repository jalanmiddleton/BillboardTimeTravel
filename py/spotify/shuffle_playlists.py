'''
The driver for the billboard scraper and storage.
'''
from random import shuffle

from secrets import secrets #pylint: disable=import-error,no-name-in-module
from spotify import Spotify, Playlist #pylint: disable=import-error

def flag_filter(flag_start="POP-START", flag_end="POP-END"):
    '''
    Return the playlists between the flags.
    '''
    def my_filter(playlist):
        if playlist["name"] in [flag_start, flag_end]:
            my_filter.between = not my_filter.between
            return False
        else:
            return my_filter.between
    my_filter.between = False
    return my_filter

def scramble(user):
    '''
    Randomly reorder a set of Spotify playlists on my account.
    The set is identified by two flags---empty playlists by a certain name---before
    and after the playlists I want.
    '''
    playlists = get_playlists(flag_filter())
    ids = [p.id for p in playlists]
    shuffle(playlists)

    for id, album in zip(ids, playlists):
        Spotify.get_instance().user_playlist_replace_tracks(user, id, album.tracks)
        Spotify.get_instance().user_playlist_change_details(user, id, album.name)


def get_playlists(filt):
    '''
    Returns the set of personal playlists as identified by a passed-in filter.
    The order by which playlists are processed is assumed to be the top-to-bottom
    order as is on the Spotify interface.

    sp: The Spotipy object
    user: The Spotify user id.
    filt: A function that returns true or false for whether the playlist qualifies.
    '''
    all_playlists = Spotify.get_instance().current_user_playlists()["items"]
    offset_now = 50
    results = []

    while len(all_playlists) > 0:
        results.extend(Playlist(p) for p in all_playlists if filt(p))
        all_playlists = Spotify.get_instance().current_user_playlists(offset=offset_now)["items"]
        offset_now += 50

    return results


if __name__ == "__main__":
    scramble(user=secrets['SPOTIFY_USER'])
