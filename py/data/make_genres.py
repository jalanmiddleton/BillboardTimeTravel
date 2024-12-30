import csv

import sys
import spotipy
from pathlib import Path
from pprint import pprint
sys.path.append(str(Path(__file__).parent.parent))
from spotify.Spotify import SpotifyItem

uri_csv = "./py/data/songlinks.csv"
genre_csv = "./py/data/songgenres.csv"
artist_genre_csv = "./py/data/artistgenres.csv"

already_artists = {}
with open(artist_genre_csv, 'r') as infile:
   genre_reader = csv.reader(infile)
   if genre_reader:
      next(genre_reader)

   for artist, *genres in genre_reader:
      already_artists[artist] = genres

already_songs = {}
with open(genre_csv, 'r') as infile:
   genre_reader = csv.reader(infile)
   next(genre_reader)

   for title, artist, *genres in genre_reader:
      already_songs[(title, artist)] = genres

with open(artist_genre_csv, 'w', newline='') as outfile:
   genre_writer = csv.writer(outfile)
   genre_writer.writerow(["artist", "genres..."])

   for (_, artist), genres in already_songs.items():
      if artist not in already_artists:
         already_artists[artist] = genres
         print([artist, *genres])
         genre_writer.writerow([artist, *genres])

with (open(uri_csv, "r") as infile, 
      open(genre_csv, "w", newline='') as outfile,
      open(artist_genre_csv, 'a', newline='') as artist_outfile):
   uri_reader = csv.reader(infile)
   next(uri_reader)

   genre_writer = csv.writer(outfile)
   genre_writer.writerow(["title", "artist", "genres..."])
   artist_genre_writer = csv.writer(artist_outfile)

   for title, artist, uri in uri_reader:
      details = (title, artist)
      genres = ['']
      if details in already_songs:
         genres = already_songs[details]
      elif artist in already_artists:
         genres = already_artists[artist]
      elif uri:         
         genres = SpotifyItem.from_uri(uri).get_genres() or ['']
         already_artists[artist] = genres       
         artist_genre_writer.writerow([artist, *genres])

      row = [*details, *genres]
      print(str(row))
      genre_writer.writerow(row)
      outfile.flush()


# track = Spotify._get_instance().track(uri)
# artist = Spotify._get_instance().artist(track['artists'][0]['uri'])
# print(artist['genres'])
