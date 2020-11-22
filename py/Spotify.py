import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
from secrets import secrets

class Spotify:
    __instance = None

    @staticmethod
    def getInstance():
        if Spotify.__instance is None:
            Spotify()

        if oauth2.is_token_expired(Spotify.__instance.__token):
            self.__token = self.__oauth_credentials.get_access_token()
            self.__sp = spotipy.Spotify(auth=self.__token,
                                        oauth_manager=self.__oauth_credentials)

        return Spotify.__instance.__sp

    def __init__(self):
        if Spotify.__instance is None:
            self.__oauth_credentials = oauth2.SpotifyOAuth(
                username=secrets['SPOTIFY_USER'],
                client_id=secrets["SPOTIPY_CLIENT_ID"],
                client_secret=secrets["SPOTIPY_SECRET"],
                redirect_uri=secrets["SPOTIPY_REDIRECT_URI"],
                scope='playlist-modify-public'
            )

            self.__token = self.__oauth_credentials.get_cached_token()
            if not self.__token or oauth2.is_token_expired(self.__token):
                self.__token = self.__oauth_credentials.get_access_token()
            self.__sp = spotipy.Spotify(auth=self.__token["access_token"],
                                        oauth_manager=self.__oauth_credentials)

            Spotify.__instance = self
