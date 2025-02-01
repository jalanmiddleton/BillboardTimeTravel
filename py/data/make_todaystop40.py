"""pyinstaller -F --paths=./py .\py\data\make_todaystop40.py"""

from datetime import date, timedelta
from pathlib import Path
from pprint import pprint
import os
import random
import sys
from typing import Optional

sys.path.append(str(Path(__file__).parent.parent))
import data.import_data as data
from spotify.Spotify import Spotify


def get_days_songs(day: Optional[date] = None) -> list[tuple[str, str, str, int]]:
    if not day:
        day = date.today()

    scores = data.get_scores()
    uris = data.get_uris()
    adjusters = data.get_adjusters()

    days_songs = []
    for song_day, _, title, artist, *_ in data.get_song_iterator():
        if song_day.day == day.day and song_day.month == day.month:
            title_artist = (title, artist)
            days_songs.append(
                (
                    title,
                    artist,
                    uris.get(title_artist, None),
                    round(
                        scores.get(title_artist, 0) * adjusters.get(song_day.year, 1),
                        2,
                    ),
                )
            )

    days_songs = sorted(days_songs, key=lambda item: item[3], reverse=True)
    return days_songs


def make_top40(
    todays_songs: list[tuple[str, str, str, int]], only_return: bool = False
) -> list[tuple[str, str, str, int]]:
    # Assumption: songs are sorted when they come in.
    past_plays = data.get_past_plays()
    one_month_ago = date.today() - timedelta(days=30)

    def skip_song(song):
        title_artist = tuple(song[:2])
        days = past_plays.get(title_artist, [])[1:]
        return (
            (title_artist in past_plays)
            and (len(days) >= 3)
            and (date.fromisoformat(days[0]) > one_month_ago)
        )
    todays_songs = [song for song in todays_songs if not skip_song(song)]

    chosen_songs = []
    chosen_songs.extend(random.sample(todays_songs[:30], 10))
    chosen_songs.extend(random.sample(todays_songs[30:60], 10))
    chosen_songs.extend(random.sample(todays_songs[60:80], 10))
    chosen_songs.extend(random.sample(todays_songs[80:100], 10))
    chosen_songs = sorted(chosen_songs, key=lambda song: song[3], reverse=True)

    if not only_return:
        Spotify.get_playlist("BB-Top40").set_tracks(
            [uri for *_, uri, _ in chosen_songs]
        )
    data.record_plays(chosen_songs)

    return chosen_songs


def make_top100(
    todays_songs: list[tuple[str, str, str, int]], only_return: bool = False
) -> list[tuple[str, str, str, int]]:
    debuts = data.get_debuts()
    top_hundred = sorted(
        todays_songs[:100], key=lambda song: debuts[(song[0], song[1])]
    )

    if not only_return:
        Spotify.get_playlist("BB-Hot100").set_tracks(
            [uri for *_, uri, _ in top_hundred]
        )
    return top_hundred


def make_genre_playlists(
    todays_songs: list[tuple[str, str, str, int]], only_return: bool = False
) -> dict[str, list[tuple[str, str, str, int]]]:
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

    top_genres = [
        key
        for key in todays_genres.keys()
        if len(todays_genres[key]) >= 20 and len(todays_genres[key]) <= 60
    ]

    chosen = {}
    genre_picks: str = random.sample(top_genres, 3)
    for genre, playlist in zip(genre_picks, Spotify.get_playlists("BB-Genre-.*")):
        genre_samples = random.sample(todays_genres[genre], 20)
        todays_picks = [uri for *_, uri in genre_samples]
        if not only_return:
            playlist.set_tracks(todays_picks)
            playlist.set_name("BB-Genre-%s" % genre.title())
        chosen[genre] = genre_samples
    return chosen


def makeplaylists(day: Optional[date] = None):
    if not day:
        day = date.today()

    days_songs = [song for song in get_days_songs(day) if song[2]]
    random.seed(day.strftime("%Y-%m-%d"))

    is_dry_run = False
    top40 = make_top40(days_songs, is_dry_run)
    top100 = make_top100(days_songs, is_dry_run)
    genres = make_genre_playlists(days_songs, is_dry_run)

    if is_dry_run:
        pprint(top40)
        pprint(top100)
        pprint(genres)


if __name__ == "__main__":
    makeplaylists()
