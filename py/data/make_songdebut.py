import csv

import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

data_csv = "../rwd-billboard-data/data-out/hot-100-current.csv"
outfile_csv = "./py/data/songdebuts.csv"

songs = {}
with open(data_csv, "r") as infile:
    reader = csv.reader(infile)
    next(reader)
    for date, _, title, artist, *_ in reader:
        key = (title, artist)  
        date = datetime.date.fromisoformat(date)
        songs[key] = min(date, songs.get(key, date.today()))

songs = sorted(songs.items(), key=lambda key_date: key_date[1])
with open(outfile_csv, "w", newline='') as outfile:
    writer = csv.writer(outfile)
    for (title, artist), date in songs:
        writer.writerow([title, artist, date.strftime("%Y-%m-%d")])
