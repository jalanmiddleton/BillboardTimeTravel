'''
Spotify wrapper.
'''
import re
from string import punctuation

from secrets import secrets #pylint: disable=import-error,no-name-in-module

import spotipy
from spotipy import oauth2
from spotipy.oauth2 import CacheFileHandler

class Spotify:
    '''
    My custom class for the Spotify utilities.
    '''
    instance = None
    __oauth = None
    __token = None

    @staticmethod
    def get_instance():
        '''
        Singleton method for this class.
        '''
        if (Spotify.instance is None or not Spotify.__oauth.validate_token(Spotify.__token)):
            Spotify.instance = None
            Spotify()
        return Spotify.instance

    def __init__(self):
        if Spotify.instance is None:
            handler = CacheFileHandler(username=secrets['SPOTIFY_USER'])
            Spotify.__oauth = oauth2.SpotifyOAuth(
                client_id=secrets["SPOTIPY_CLIENT_ID"],
                client_secret=secrets["SPOTIPY_SECRET"],
                redirect_uri=secrets["SPOTIPY_REDIRECT_URI"],
                scope='playlist-modify-public',
                cache_handler=handler
            )
            Spotify.__token = Spotify.__oauth.get_access_token(as_dict=False)
            Spotify.instance = spotipy.Spotify(auth=Spotify.__token,
                                               oauth_manager=self.__oauth)

    @staticmethod
    def search(item_type, title, artist):
        '''
        Search for a given item on Spotify.
        '''
        if item_type not in ["track", "album"]:
            raise ValueError(f"Unknown type of Spotify item: {item_type}")

        title_bb    = title.lower().strip()
        artist_bb   = artist.lower().strip() if artist else ""
        query       = Spotify.get_query(title, artist)
        failed      = []

        searchresults = Spotify.get_instance().search(q=query, type=item_type, limit=10)
        for result in searchresults[item_type + "s"]["items"]:
            title_spotify = Spotify.remove_parens(result["name"].lower())
            if Spotify.has_unique_words(title_bb, title_spotify, ["cover", "karaoke", "remix"]):
                continue

            artist_spotify = result["artists"][0]["name"].lower()
            if Spotify.has_unique_words(artist_bb, artist_spotify, ["tribute", "karaoke"]):
                break

            if (artist_bb == "soundtrack" or Spotify.lss_match(artist_bb, artist_spotify) >= .75) \
                and Spotify.lss_match(title_bb, title_spotify) >= .75:
                return SpotifyItem(item_type, title, artist, result)

            failed.append(f"\t\"{title_spotify}\" by {result['artists'][0]['name']}")

        return SpotifyItem(item_type, title, artist)

    @staticmethod
    def get_query(title, artist):
        '''
        Turns the title and artist into a Spotify search query.
        '''
        artist = " ".join(filter(
            lambda word: (
                "feat" not in word
                and word not in punctuation
            ), artist.lower().split()))
        return Spotify.remove_parens(title) + " " + " ".join(re.split(r"\s|,", artist)[:3])

    @staticmethod
    def remove_parens(string):
        '''
        Removes parentheticals from strings.
        '''
        return re.sub(r"\(.+\)|\[.+\]", "", string)

    @staticmethod
    def has_unique_words(original, result, words):
        '''
        Checks if any of a given word appears in only one of original or result.
        Useful for filtering out covers and karaoke version.
        '''
        return any(word in original != word in result for word in words)

    @staticmethod
    def lss_match(one, two):
        '''
        Longest substring --- how much of the smaller string can be found in the larger string?
        '''
        shortest, longest = (one, two) if len(one) < len(two) else (two, one)
        if len(shortest) == 0:
            return 0

        matrix = [[0 for _ in range(len(shortest) + 1)] for _ in range(len(longest) + 1)]
        for x in range(1, len(longest) + 1):        #pylint:disable=invalid-name
            for y in range(1, len(shortest) + 1):   #pylint:disable=invalid-name
                matrix[x][y] = (matrix[x - 1][y - 1] + 1) \
                    if longest[x - 1] == shortest[y - 1] \
                    else max(matrix[x - 1][y], matrix[x][y - 1])

        return float(matrix[-1][-1]) / len(shortest)

class SpotifyItem():
    '''
    Encapsulation of an item to search for on Spotify.
    '''
    def __init__(self, item_type, title, artist, searchres=None):
        super().__init__()
        self.type           = item_type
        self.title          = title
        self.artist         = artist

        self.uri            = searchres["uri"] if searchres else None
        self.title_spotify  = searchres["name"] if searchres else None
        self.artist_spotify = (",".join(x["name"] for x in searchres["artists"])
                               if searchres else None)
        self.popularity     = ((searchres["popularity"] if "popularity" in searchres
                                else None) if searchres else None)
        self.duration       = (((sum(track["duration_ms"] for track in searchres["tracks"]["items"])
                                 if "tracks" in searchres else -1)
                                if item_type == "album" else searchres["duration_ms"])
                               if searchres else None)
        self.problem        = "Not found." if searchres is None else None

        #I'd love genres, but they don't seem to work.
        #self.genres         = ((",".join(searchres["genres"]) if "genres" in searchres else None)
        #                       if searchres else None)

    def get_details(self):
        '''
        Returns a dictionary of all fields in this class.
        '''
        return  { field:getattr(self, field) for field in dir(self)
                  if field[0] != "_" and field != "get_details" }
