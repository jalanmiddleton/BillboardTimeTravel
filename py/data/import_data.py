import csv
from datetime import date
import os.path as path
from typing import Generator, Optional

dirpath = ""  # C:/Users/jalan/git/BillboardTimeTravel/"


def get_scores() -> dict[tuple[str, str], int]:
    score_csv = path.join(dirpath, "./py/data/top40score.csv")
    scores = {}
    with open(score_csv, "r") as score_infile:
        score_reader = csv.reader(score_infile)
        next(score_reader)
        for title, artist, score in score_reader:
            scores[(title, artist)] = int(score)
    return scores


def get_uris() -> dict[tuple[str, str], str]:
    uri_csv = path.join(dirpath, "./py/data/songlinks.csv")
    uris = {}
    with open(uri_csv, "r") as uri_infile:
        uri_reader = csv.reader(uri_infile)
        next(uri_reader)
        for title, artist, uri in uri_reader:
            uris[(title, artist)] = uri
    return uris


def get_adjusters() -> dict[tuple[str, str], float]:
    adj_csv = path.join(dirpath, "./py/data/yearadjuster.csv")
    adjusters = {}
    with open(adj_csv, "r") as adj_infile:
        adj_reader = csv.reader(adj_infile)
        next(adj_reader)
        for year, adj in adj_reader:
            adjusters[int(year)] = float(adj)
    return adjusters


def get_debuts() -> dict[tuple[str, str], Optional[date]]:
    debuts_csv = path.join(dirpath, "./py/data/songdebuts.csv")
    debuts = {}
    with open(debuts_csv, "r") as debuts_infile:
        debuts_reader = csv.reader(debuts_infile)
        next(debuts_reader)
        for *title_artist, debut in debuts_reader:
            title_artist = tuple(title_artist)
            debut = date.fromisoformat(debut)
            if title_artist not in debuts:
                debuts[title_artist] = debut
            if debut < debuts[title_artist]:
                debuts[title_artist] = date.fromisoformat(debut)
    return debuts


def get_genres() -> dict[tuple[str, str], list[str]]:
    genre_csv = path.join(dirpath, "./py/data/songgenres.csv")
    genres = {}
    with open(genre_csv, "r") as genre_infile:
        genre_reader = csv.reader(genre_infile)
        next(genre_reader)
        for song, artist, *gs in genre_reader:
            genres[(song, artist)] = gs
    return genres


def get_penalties() -> dict[tuple[str, str], int]:
    return {}


def get_song_iterator() -> Generator[tuple[date, int, str, str, int, int, int]]:
    # chart_week,current_week,title,performer,last_week,peak_pos,wks_on_chart
    song_csv = path.join(dirpath, "../rwd-billboard-data/data-out/hot-100-current.csv")
    with open(song_csv, "r") as song_infile:
        song_reader = csv.reader(song_infile)
        next(song_infile)

        for (
            chart_week,
            current_week,
            title,
            performer,
            last_week,
            peak_pos,
            wks_on_chart,
        ) in song_reader:
            chart_week = date.fromisoformat(chart_week)
            current_week, last_week, peak_pos, wks_on_chart = map(
                int,
                [
                    current_week,
                    last_week if last_week != "NA" else "-1",
                    peak_pos,
                    wks_on_chart,
                ],
            )
            yield chart_week, current_week, title, performer, last_week, peak_pos, wks_on_chart


def penalize(list[tuple[str, str, str, int]]) -> None:
    pass


if __name__ == "__main__":
    print(list(get_scores().items())[:5])
