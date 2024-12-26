import csv

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from spotify.Spotify import Spotify

# data_csv = "../rwd-billboard-data/data-out/hot100_archive_1958_2021.csv"
data_csv = "../rwd-billboard-data/data-out/hot-100-current.csv"
outfile_csv = "./py/data/songlinks.csv"

cache = set()
with open(outfile_csv, "r") as already:
    next(already)
    for line in csv.reader(already):
        if not line:
            continue
        title, artist = line[0], line[1]
        cache.add(Spotify._get_query(title, artist))

with open(data_csv, "r") as infile, open(outfile_csv, "a") as outfile:
    writer = csv.writer(outfile)
    if not cache:
        writer.writerow(["title", "artist", "uri"])
    next(infile) # skip the first line

    for line in csv.reader(infile):
        print(line)
        title, artist = line[2], line[3]
        query = Spotify._get_query(title, artist)
        if query in cache:
            continue
        
        uri = Spotify.search(title, artist).uri
        cache.add(query)
        writer.writerow([title, artist, uri])
        outfile.flush()
        