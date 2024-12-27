import csv

import random
import sys
import datetime
from pathlib import Path
from pprint import pprint
sys.path.append(str(Path(__file__).parent.parent))
from spotify.Spotify import Spotify

song_csv = "../rwd-billboard-data/data-out/hot-100-current.csv"
score_csv = "./py/data/top40score.csv"
uri_csv = "./py/data/songlinks.csv"
adj_csv = "./py/data/yearadjuster.csv"

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
todays_songs = [x for x in todays_songs if x[1][1]]  # if uri is not None

chosen_songs = []
random.seed(today.strftime("%Y-%m-%d"))
chosen_songs.extend(random.sample(todays_songs[:40], 20))
chosen_songs.extend(random.sample(todays_songs[40:70], 10))
chosen_songs.extend(random.sample(todays_songs[70:100], 10))
chosen_songs = sorted(chosen_songs, key=lambda item: item[1][0], reverse=True)
chosen_songs = [uri for _, (_, uri) in chosen_songs if uri]

# All top ten
Spotify.get_playlist().set_tracks(chosen_songs)
