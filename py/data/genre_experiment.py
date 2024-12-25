import csv

import sys
from pathlib import Path
from pprint import pprint
sys.path.append(str(Path(__file__).parent.parent))
from spotify.Spotify import SpotifyItem

uri_csv = "./py/data/songlinks.csv"
with open(uri_csv, "r") as uri_infile:
    uri_reader = csv.reader(uri_infile)
    next(uri_reader)

    num_tries = 40
    while (num_tries := num_tries - 1) >= 0:
     *details, uri = next(uri_reader)
     if not uri:
        num_tries += 1
        continue
     print("%s %s" % (str(details), str(SpotifyItem.from_uri(uri).get_genres())))

# track = Spotify._get_instance().track(uri)
# artist = Spotify._get_instance().artist(track['artists'][0]['uri'])
# print(artist['genres'])
