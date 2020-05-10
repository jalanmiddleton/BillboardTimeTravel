import MySQLdb
import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
from secrets import secrets

_conn = None
_cur = None
_token = None
_credentials = oauth2.SpotifyClientCredentials(
    client_id=secrets["SPOTIPY_CLIENT_ID"],
    client_secret=secrets["SPOTIPY_SECRET"]
)


def InitDB():
    global _conn, _cur
    _conn = MySQLdb.connect(host="localhost", user="root",
                            passwd=secrets["HOST_PASSWORD"], db="billboard",
                            use_unicode=True, charset="utf8")
    _cur = _conn.cursor()
    return _conn, _cur

# Defining Spotify.sp allows persistence

def insert(query):
    global _conn, _cur
    _cur.execute(query)
    _conn.commit()

def select(query):
    global _conn, _cur
    _cur.execute(query)
    return _cur.fetchall()


def Spotify():
    # Scopes here: https://developer.spotify.com/documentation/general/guides/scopes/
    if not _token or _credentials.is_token_expired(_token):
        token = util.prompt_for_user_token(secrets['SPOTIFY_USER'],
                                           client_id=secrets["SPOTIPY_CLIENT_ID"],
                                           client_secret=secrets["SPOTIPY_SECRET"],
                                           redirect_uri=secrets["SPOTIPY_REDIRECT_URI"],
                                           scope='playlist-modify-public')
        Spotify.sp = spotipy.Spotify(auth=token,
                                     client_credentials_manager=_credentials)
    return Spotify.sp

Spotify.sp = None

### Below are things I don't have a good place for.

def truncate_all():
    global _conn, _cur
    _cur.execute(
            "truncate albums; truncate `billboard-200`; truncate `hot-100`; \
		truncate tracks;")
    _cur.close()
    _cur = _conn._cursor()


def fill_in_uris():
    global _conn, _cur
    _cur.execute("SELECT * FROM songs where id not in (SELECT id FROM uris)")
    for song in _cur.fetchall():
        print(song)

        uri = get_song_link(song[1], song[2])
        if uri:
            newuri = "INSERT IGNORE INTO billboard.uris (id, uri, song, artist)\
				VALUES (%s, '%s', '%s', '%s')" \
                    % (song[0], uri["uri"], sql_prep(uri['title']),
                       sql_prep(uri['artist']))
            _cur.execute(newuri)
            _cur.execute("UPDATE billboard.songs SET song='%s', popularity = %s\
				where id = %s" % (song[1].replace("'", "\\'"),
                      uri["popularity"], song[0]))
            _conn.commit()
