import csv

import sys
from pathlib import Path
from pprint import pprint
sys.path.append(str(Path(__file__).parent.parent))
from spotify.Spotify import SpotifyItem

uri_csv = "./py/data/songlinks.csv"
genre_csv = "./py/data/songgenres.csv"

already = {}
with open(genre_csv, 'r') as infile:
   genre_reader = csv.reader(infile)
   next(genre_reader)

   for title, artist, *genres in genre_reader:
      already[(title, artist)] = genres

with open(uri_csv, "r") as infile, open(genre_csv, "w", newline='') as outfile:
   uri_reader = csv.reader(infile)
   next(uri_reader)
   genre_writer = csv.writer(outfile)
   genre_writer.writerow(["title", "artist", "genres..."])
   for *details, uri in uri_reader:
      if details in already:
         genres = already[details]
      else:
         genres = SpotifyItem.from_uri(uri).get_genres() if uri else ['']
         if not genres:
            genres = ['']

      row = [*details, *genres]
      print(str(row))
      genre_writer.writerow(row)
      outfile.flush()


# track = Spotify._get_instance().track(uri)
# artist = Spotify._get_instance().artist(track['artists'][0]['uri'])
# print(artist['genres'])
