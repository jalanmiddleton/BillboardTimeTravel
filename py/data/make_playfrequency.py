import csv
from datetime import date, timedelta
from pathlib import Path
import random
import sys

sys.path.append(str(Path(__file__).parent.parent))
import data.make_todaystop40 as playlist_maker

outfile_csv = "./py/data/songplays.csv"
day = date.fromisoformat('2025-01-01')
end = date.today()

plays = {}
while day <= end:
    print(day)

    songs = playlist_maker.get_days_songs(day)
    random.seed(day.strftime("%Y-%m-%d"))
    top40 = playlist_maker.make_top40(songs, True)
    
    for song in top40:
        song = song[:2]
        if song not in plays:
            plays[song] = []
        plays[song].append(day)

    day += timedelta(days=1)

with open(outfile_csv, "w", newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(["title", "artist", "plays..."])
    
    for title_artist in plays:
        writer.writerow([*title_artist, *plays[title_artist]])
