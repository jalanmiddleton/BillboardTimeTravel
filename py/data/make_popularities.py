import csv
from datetime import date, timedelta
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
import data.import_data as data
from spotify.Spotify import SpotifyItem

pops_csv = "./py/data/popularities.csv"
pops = data.get_popularities()

one_week_ago = date.today() - timedelta(days=7)
songs = data.get_uris()

with open(pops_csv, "w", newline='') as pops_outfile:
    writer = csv.writer(pops_outfile)
    writer.writerow(["song", "artist", "days...", "popularities..."])

    for song_artist, uri in songs.items():
        if not uri:
            continue

        print(song_artist)
        past_pops = pops.get(song_artist, [])

        if not past_pops or (past_pops[-2] < one_week_ago):
            pop = SpotifyItem.from_uri(uri).get_popularity()
            past_pops.extend([date.today(), pop])

        for day_idx in range(0, len(past_pops), 2):
            past_pops[day_idx] = past_pops[day_idx].strftime("%Y-%m-%d")
        writer.writerow([*song_artist, *past_pops])
        pops_outfile.flush()

