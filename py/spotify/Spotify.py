"""
Spotify wrapper.
"""

import re
from pprint import pprint, pformat
from string import punctuation
from typing import Generator, Sequence

from .secrets import secrets  # pylint: disable=import-error,no-name-in-module

import spotipy
from spotipy import oauth2
from spotipy.oauth2 import CacheFileHandler


class SpotifyItem:
    """
    Encapsulation of an item to search for on Spotify.
    """

    def __init__(self, item_type, title, artist, searchres=None):
        super().__init__()
        self.type = item_type
        self.title = title
        self.artist = artist

        self.uri = searchres["uri"] if searchres else None
        self.title_spotify = searchres["name"] if searchres else None
        self.artist_spotify = (
            ",".join(x["name"] for x in searchres["artists"]) if searchres else None
        )
        self.popularity = (
            (searchres["popularity"] if "popularity" in searchres else None)
            if searchres
            else None
        )
        self.duration = (
            (
                (
                    sum(track["duration_ms"] for track in searchres["tracks"]["items"])
                    if "tracks" in searchres
                    else -1
                )
                if item_type == "album"
                else searchres["duration_ms"]
            )
            if searchres
            else None
        )
        self.problem = "Not found." if searchres is None else None


    def get_details(self):
        """
        Returns a dictionary of all fields in this class.
        """
        return {
            field: getattr(self, field)
            for field in dir(self)
            if field[0] != "_" and field != "get_details"
        }
    
    def __repr__(self):
        return pformat(self.get_details())


class Playlist:
    def __init__(self, partial_playlist):
        playlist = Spotify.get_instance().playlist(
            partial_playlist["id"], fields="id,name,tracks,uri,next"
        )

        self.id = playlist["id"]
        self.name = playlist["name"]
        self.tracks = [t["track"]["uri"] for t in playlist["tracks"]["items"]]
        self.uri = playlist["uri"]


class Spotify:
    """
    My custom class for the Spotify utilities.
    """

    instance = None
    __oauth = None
    __token = None

    DEFAULT_PLAYLIST = "BB-DEFAULT"

    @staticmethod
    def get_instance():
        """
        Singleton method for this class.
        """
        if Spotify.instance is None or not Spotify.__oauth.validate_token(
            Spotify.__token
        ):
            Spotify.instance = None
            Spotify()
        return Spotify.instance

    def __init__(self):
        if Spotify.instance is None:
            handler = CacheFileHandler(username=secrets["SPOTIFY_USER"])
            Spotify.__oauth = oauth2.SpotifyOAuth(
                client_id=secrets["SPOTIPY_CLIENT_ID"],
                client_secret=secrets["SPOTIPY_SECRET"],
                redirect_uri=secrets["SPOTIPY_REDIRECT_URI"],
                scope="playlist-modify-public",
                cache_handler=handler,
            )
            Spotify.__token = Spotify.__oauth.get_access_token(as_dict=False)
            Spotify.instance = spotipy.Spotify(
                auth=Spotify.__token, oauth_manager=self.__oauth
            )

    @staticmethod
    def _get_BB_playlists() -> Generator["Playlist"]:
        prefix = "BB-"
        offset = 0
        while (
            playlists := Spotify.get_instance().user_playlists(
                user=secrets["SPOTIFY_USER"], offset=offset
            )
        )['items']:
            for playlist in playlists['items']:
                if playlist['name'].startswith(prefix):
                    yield Playlist(playlist)
            offset += 50

        return None

    @staticmethod
    def get_playlist(name: str = DEFAULT_PLAYLIST) -> "Playlist":
        return next((pl for pl in Spotify._get_BB_playlists() if pl.name == name), None)

    @staticmethod
    def get_playlists(pattern: str = DEFAULT_PLAYLIST) -> Sequence["Playlist"]:
        return [pl for pl in Spotify._get_BB_playlists() if re.match(pattern, pl.name)]

    @staticmethod
    def search(title, artist, item_type="track"):
        """
        Search for a given item on Spotify.
        """
        if item_type not in ["track", "album"]:
            raise ValueError(f"Unknown type of Spotify item: {item_type}")

        query = Spotify.get_query(title, artist)
        failed = []

        searchresults = Spotify.get_instance().search(q=query, type=item_type, limit=10)
        for result in searchresults[item_type + "s"]["items"]:
            title_spotify = result["name"]
            if Spotify.has_unique_words(
                title, title_spotify, ["cover", "karaoke", "remix"]
            ):
                continue

            artist_spotify = result["artists"][0]["name"]
            if Spotify.has_unique_words(
                artist, artist_spotify, ["tribute", "karaoke"]
            ):
                continue

            if Spotify.lss_match(artist, artist_spotify) >= 0.6 and Spotify.lss_match(title, title_spotify) >= 0.6:
                return SpotifyItem(item_type, title, artist, result)

            failed.append(f"\t\"{title_spotify}\" by {result['artists'][0]['name']}")

        return SpotifyItem(item_type, title, artist)

    @staticmethod
    def get_query(title: str, artist: str):
        """
        Turns the title and artist into a Spotify search query.
        """
        title = title.replace("%", "")
        artist = re.sub(r"((f|F)eat|(w|W)ith| (x|X) | & ).*$", "", artist)
        return f'track:"{title}" artist:"{artist}"'

    @staticmethod
    def has_unique_words(original: str, result: str, words):
        """
        Checks if any of a given word appears in only one of original or result.
        Useful for filtering out covers and karaoke version.
        """
        return any(word in original.lower() != word in result.lower() for word in words)

    @staticmethod
    def lss_match(one: str, two: str):
        """
        Longest substring --- how much of the smaller string can be found in the larger string?
        """
        shortest, longest = (one, two) if len(one) < len(two) else (two, one)
        shortest, longest = shortest.lower(), longest.lower()

        if len(shortest) == 0:
            return 0

        matrix = [
            [0 for _ in range(len(shortest) + 1)] for _ in range(len(longest) + 1)
        ]
        for x in range(1, len(longest) + 1):  # pylint:disable=invalid-name
            for y in range(1, len(shortest) + 1):  # pylint:disable=invalid-name
                matrix[x][y] = (
                    (matrix[x - 1][y - 1] + 1)
                    if longest[x - 1] == shortest[y - 1]
                    else max(matrix[x - 1][y], matrix[x][y - 1])
                )

        return float(matrix[-1][-1]) / len(shortest)

