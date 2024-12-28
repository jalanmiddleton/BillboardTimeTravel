"""
Spotify wrapper.
"""

import re
from pathlib import Path
from pprint import pprint, pformat
from string import punctuation
import sys
from typing import Generator, Sequence

sys.path.append(str(Path(__file__).parent.parent))
from spotify.secrets import secrets

import spotipy
from spotipy import oauth2
from spotipy.oauth2 import CacheFileHandler


class SpotifyItem:
    """
    Encapsulation of an item to search for on Spotify.
    """

    @staticmethod
    def from_uri(uri):
        itemtype = uri.split(":")[1]

        if itemtype == "track":
            searchres = Spotify._get_instance().track(uri)
        else:
            searchres = Spotify._get_instance().album(uri)
        
        return SpotifyItem(searchres)

    def __init__(self, searchres):
        super().__init__()

        if not searchres:
            return 

        self.uri = searchres["uri"]
        self.type = self.uri.split(":")[1]
        self.title = searchres["name"]
        self.artist =  ",".join(x["name"] for x in searchres["artists"])

        self.popularity = (searchres["popularity"] if "popularity" in searchres else None)
        self.duration = (
            (
                sum(track["duration_ms"] for track in searchres["tracks"]["items"])
                if "tracks" in searchres
                else -1
            )
            if self.type != "track"
            else searchres["duration_ms"]
        )

    def get_details(self):
        """
        Returns a dictionary of all fields in this class.
        """
        return {
            field: getattr(self, field)
            for field in dir(self)
            if field[0] != "_" and field != "get_details"
        }
    
    def get_genres(self):
        track = Spotify._get_instance().track(self.uri)
        artist = Spotify._get_instance().artist(track['artists'][0]['uri'])
        return artist['genres']
    
    def __repr__(self):
        return pformat(self.get_details())

class MissingSpotifyItem(SpotifyItem):
    """
    Encapsulation of an item to search for on Spotify.
    """

    def __init__(self, title: str, artist: str, item_type: str):
        super().__init__(None)
        self.uri = None
        self.title = title
        self.artist = artist
        self.type = item_type

        self.popularity = -1
        self.duration = -1


class Playlist:
    def __init__(self, spotipy_reference):
        playlist = Spotify._get_instance().playlist(
            spotipy_reference["id"], fields="id,name,tracks,uri,next"
        )

        self.id = playlist["id"]
        self.name = playlist["name"]
        self.tracks = [t["track"]["uri"] for t in playlist["tracks"]["items"]]
        self.uri = playlist["uri"]

    def set_tracks(self, tracks: Sequence[str]):
        s = Spotify._get_instance()

        if self.tracks:
            s.user_playlist_remove_all_occurrences_of_tracks(           
                user=secrets["SPOTIFY_USER"],
                playlist_id=self.id,
                tracks=self.tracks
            )

        result = s.user_playlist_replace_tracks(
            user=secrets["SPOTIFY_USER"],
            playlist_id=self.id,
            tracks=tracks
        )

        self.tracks = tracks


class Spotify:
    """
    My custom class for the Spotify utilities.
    """

    instance: spotipy.Spotify = None
    __oauth = None
    __token = None

    DEFAULT_PLAYLIST = "BB-DEFAULT"

    @staticmethod
    def _get_instance() -> spotipy.Spotify:
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
            playlists := Spotify._get_instance().user_playlists(
                user=secrets["SPOTIFY_USER"], offset=offset
            )
        )['items']:
            for playlist in playlists['items']:
                if playlist['name'].startswith(prefix):
                    yield Playlist(playlist)
            offset += 50

        return None

    @staticmethod
    def get_playlist(pattern: str = DEFAULT_PLAYLIST) -> "Playlist":
        return next((pl for pl in Spotify._get_BB_playlists() if re.match(pattern, pl.name)), None)

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

        query = Spotify._get_query(title, artist)
        failed = []

        searchresults = Spotify._get_instance().search(q=query, type=item_type, limit=10)
        for result in searchresults[item_type + "s"]["items"]:
            title_spotify = result["name"]
            if Spotify._has_unique_words(
                title, title_spotify, ["cover", "karaoke", "remix"]
            ):
                continue

            artist_spotify = result["artists"][0]["name"]
            if Spotify._has_unique_words(
                artist, artist_spotify, ["tribute", "karaoke"]
            ):
                continue

            if Spotify._lss_match(artist, artist_spotify) >= 0.6 and Spotify._lss_match(title, title_spotify) >= 0.6:
                return SpotifyItem(result)

            failed.append(f'\t"{title_spotify}" by {result['artists'][0]['name']}')

        return MissingSpotifyItem(title, artist, item_type)

    @staticmethod
    def _get_query(title: str, artist: str):
        """
        Turns the title and artist into a Spotify search query.
        """
        title = "".join(c for c in title if c not in punctuation)  # crashed with "100% Pure Love,Crystal Waters"
        artist = re.sub(r" ((f|F)eat|(w|W)ith|(a|A)nd|(x|X)|&).*$", "", artist)
        return f'track:"{title}" artist:"{artist}"'

    @staticmethod
    def _has_unique_words(original: str, result: str, words):
        """
        Checks if any of a given word appears in only one of original or result.
        Useful for filtering out covers and karaoke version.
        """
        return any(word in original.lower() != word in result.lower() for word in words)

    @staticmethod
    def _lss_match(one: str, two: str):
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

