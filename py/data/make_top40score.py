import csv

import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from spotify.Spotify import Spotify

data_csv = "../rwd-billboard-data/data-out/hot-100-current.csv"
outfile_csv = "./py/data/top40score.csv"

songs = {}
with open(data_csv, "r") as infile:
    reader = csv.reader(infile)
    next(infile)  # skip first line
    for _, place, title, artist, *_ in reader:
        key = (title, artist)  
        if int(place) <= 40:
            songs[key] = songs.get(key, 0) + 1

with open(outfile_csv, "w") as outfile:
    writer = csv.writer(outfile)
    for title_artist in sorted(songs.keys()):
        writer.writerow([*title_artist, songs[title_artist]])
