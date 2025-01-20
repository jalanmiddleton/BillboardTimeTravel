import csv

import random
import sys
import datetime
from pathlib import Path

import import_data as data

spotify_path = Path(__file__).parents[1]
sys.path.append(str(spotify_path))
from spotify import Spotify


def get_todays_songs() -> list[tuple[str, str, str, int]]:
    scores = data.get_scores()
    uris = data.get_uris()
    adjusters = data.get_adjusters()
    penalties = data.get_penalties()

    today = datetime.date.today()
    todays_songs = []
    for day, _, title, artist, *_ in data.get_song_iterator():
        if day.day == today.day and day.month == today.month:
            title_artist = (title, artist)
            todays_songs.append(
                (
                    title,
                    artist,
                    uris.get(title_artist, None),
                    scores.get(title_artist, 0) * adjusters.get(day.year, 1)
                    - penalties.get(title_artist, 0),
                )
            )

    todays_songs = sorted(todays_songs, key=lambda item: item[3], reverse=True)
    return todays_songs


def make_top40(todays_songs: list[tuple[str, str, str, int]]) -> None:
    chosen_songs = []
    chosen_songs.extend(random.sample(todays_songs[:30], 10))
    chosen_songs.extend(random.sample(todays_songs[30:60], 10))
    chosen_songs.extend(random.sample(todays_songs[60:80], 10))
    chosen_songs.extend(random.sample(todays_songs[80:100], 10))
    chosen_songs = sorted(chosen_songs, key=lambda song: song[3], reverse=True)
    Spotify.get_playlist("BB-Top40").set_tracks([uri for *_, uri, _ in chosen_songs])


def make_top100(todays_songs: list[tuple[str, str, str, int]]) -> None:
    debuts = data.get_debuts()
    top_hundred = sorted(
        todays_songs[:100], key=lambda song: debuts[(song[0], song[1])]
    )
    Spotify.get_playlist("BB-Hot100").set_tracks([uri for *_, uri, _ in top_hundred])


def make_genre_playlists(todays_songs: list[tuple[str, str, str, int]]):
    genres = data.get_genres()
    todays_genres = {}
    for song, artist, uri, _ in todays_songs:
        if (song, artist) not in genres:
            continue

        for genre in genres[(song, artist)]:
            if genre not in todays_genres:
                todays_genres[genre] = []
            if uri:
                todays_genres[genre].append((song, artist, uri))

    top_genres = sorted(
        [
            key
            for key in todays_genres.keys()
            if len(todays_genres[key]) >= 20 and len(todays_genres[key]) <= 60
        ],
        key=lambda key: len(todays_genres[key]),
        reverse=True,
    )

    genre_picks: str = random.sample(top_genres, 3)
    for genre, playlist in zip(genre_picks, Spotify.get_playlists("BB-Genre-.*")):
        todays_picks = [uri for *_, uri in random.sample(todays_genres[genre], 20)]
        playlist.set_tracks(todays_picks)
        Spotify._get_instance().playlist_change_details(
            playlist_id=playlist.id, name="BB-Genre-%s" % genre.title()
        )


def makeplaylists():
    today = datetime.date.today()
    todays_songs = [song for song in get_todays_songs() if song[2]]
    random.seed(today.strftime("%Y-%m-%d"))

    make_top40(todays_songs)
    make_top100(todays_songs)
    make_genre_playlists(todays_songs)


if __name__ == "__main__":
    makeplaylists()
