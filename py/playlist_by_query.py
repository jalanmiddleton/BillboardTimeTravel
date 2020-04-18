from core import _cur, Spotify, InitDB
from main import findplaylists
from secrets import secrets

query = """SELECT
        spoffy_title,
        spoffy_artist,
        uri,
        YEAR(week),
        (popularity + SQRT(SUM(i)) / SQRT(5676) * 100) / 2 points
    FROM
        (SELECT
            *, 101 - idx i
        FROM
            billboard.`hot-100` h
        JOIN tracks t ON item_id = id
        WHERE
            YEAR(h.week) >= 1990
                AND YEAR(h.week) <= 1999
                AND uri IS NOT NULL) nineties_hits
    GROUP BY uri
    ORDER BY points DESC
    LIMIT 50; """

_, cur = InitDB()
cur.execute(query)
songs = cur.fetchall()
songs = [x[2] for x in songs]
playlist = findplaylists(secrets['SPOTIFY_USER'],
                         lambda x: x["name"].startswith("BB"))[0].uri
Spotify().user_playlist_replace_tracks(
    secrets['SPOTIFY_USER'], playlist, songs)
