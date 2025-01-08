import csv

import random
import sys
import datetime
import os.path as path

sys.path.append("C:/Users/jalan/git/BillboardTimeTravel/py/spotify")
from Spotify import Spotify

def makeplaylists():
    dirpath = "C:/Users/jalan/git/BillboardTimeTravel/"
    song_csv = path.join(dirpath, "../rwd-billboard-data/data-out/hot-100-current.csv")
    score_csv = path.join(dirpath, "./py/data/top40score.csv")
    uri_csv = path.join(dirpath, "./py/data/songlinks.csv")
    adj_csv = path.join(dirpath, "./py/data/yearadjuster.csv")
    debuts_csv = path.join(dirpath, "./py/data/songdebuts.csv")

    scores = {}
    with open(score_csv, "r") as score_infile:
        score_reader = csv.reader(score_infile)
        next(score_reader)
        for title, artist, score in score_reader:
            scores[(title, artist)] = int(score)

    uris = {}
    with open(uri_csv, "r") as uri_infile:
        uri_reader = csv.reader(uri_infile)
        next(uri_reader)
        for title, artist, uri in uri_reader:
            uris[(title, artist)] = uri

    adjusters = {}
    with open(adj_csv, "r") as adj_infile:
        adj_reader = csv.reader(adj_infile)
        next(adj_reader)
        for year, adj in adj_reader:
            adjusters[int(year)] = float(adj)

    today = datetime.date.today()
    todays_songs = {}
    with open(song_csv, "r") as song_infile:
        song_reader = csv.reader(song_infile)
        next(song_infile)
        for day, _, title, artist, *_ in song_reader:
            day = datetime.date.fromisoformat(day)
            key = (title, artist)
            if day.day == today.day and day.month == today.month:
                todays_songs[key] = (scores.get(key, 0) * adjusters[day.year], uris.get(key, None))

    todays_songs = sorted(todays_songs.items(), key=lambda item: item[1][0], reverse=True)
    todays_songs = [x for x in todays_songs if x[1][1]][:100]  # if uri is not None

    chosen_songs = []
    random.seed(today.strftime("%Y-%m-%d    "))
    chosen_songs.extend(random.sample(todays_songs[:30], 10))
    chosen_songs.extend(random.sample(todays_songs[30:60], 10))
    chosen_songs.extend(random.sample(todays_songs[60:80], 10))
    chosen_songs.extend(random.sample(todays_songs[80:100], 10))
    chosen_songs = sorted(chosen_songs, key=lambda item: item[1][0], reverse=True)
    chosen_songs = [uri for _, (_, uri) in chosen_songs]

    # All top ten
    Spotify.get_playlist("BB-Top40").set_tracks(chosen_songs)

    debuts = {title_artist: None for title_artist, _ in todays_songs}
    with open(debuts_csv, "r") as debuts_infile:
        debuts_reader = csv.reader(debuts_infile)
        next(debuts_reader)
        for *title_artist, debut in debuts_reader:
            title_artist = tuple(title_artist)
            if title_artist in debuts:
                debuts[title_artist] = datetime.date.fromisoformat(debut)
    todays_songs = sorted(todays_songs, key=lambda data: debuts[data[0]])
    Spotify.get_playlist("BB-Hot100").set_tracks([uri for _, (_, uri) in todays_songs])

if __name__ == "__main__":
    makeplaylists()
