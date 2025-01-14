import csv

import random
import sys
import datetime
import os.path as path

sys.path.append("C:/Users/jalan/git/BillboardTimeTravel/py/spotify")
from Spotify import Spotify

dirpath = "C:/Users/jalan/git/BillboardTimeTravel/"

def get_todays_songs() -> dict[tuple, tuple]:
    song_csv = path.join(dirpath, "../rwd-billboard-data/data-out/hot-100-current.csv")
    score_csv = path.join(dirpath, "./py/data/top40score.csv")
    uri_csv = path.join(dirpath, "./py/data/songlinks.csv")
    adj_csv = path.join(dirpath, "./py/data/yearadjuster.csv")

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
    todays_songs = []
    with open(song_csv, "r") as song_infile:
        song_reader = csv.reader(song_infile)
        next(song_infile)
        for day, _, title, artist, *_ in song_reader:
            day = datetime.date.fromisoformat(day)
            if day.day == today.day and day.month == today.month:
                todays_songs.append((title, 
                                     artist, 
                                     uris.get((title, artist), None), 
                                     scores.get((title, artist), 0) * adjusters[day.year]))

    todays_songs = sorted(todays_songs, key=lambda item: item[3], reverse=True)
    return todays_songs

def make_genre_playlist():
    todays_songs = get_todays_songs()

    genre_csv = path.join(dirpath, "./py/data/songgenres.csv")
    genres = {}
    with open(genre_csv, "r") as genre_infile:
        genre_reader = csv.reader(genre_infile)
        next(genre_reader)
        for song, artist, *gs in genre_reader:
            genres[(song, artist)] = gs

    todays_genres = {}
    for song, artist, uri, _ in todays_songs:
        for genre in genres[(song, artist)]:
            if genre not in todays_genres:
                todays_genres[genre] = []
            if uri:
                todays_genres[genre].append((song, artist, uri))
    
    top_genres = sorted([key for key in todays_genres.keys() if len(todays_genres[key]) >= 20 and len(todays_genres[key]) <= 60],
                           key = lambda key: len(todays_genres[key]), 
                           reverse=True)
    
    todays_genre: str = random.sample(top_genres, 1)[0]
    todays_picks = [uri for *_, uri in random.sample(todays_genres[todays_genre], 20)]
    Spotify.get_playlist("BB-Genre-.*").set_tracks(todays_picks)    
    Spotify._get_instance().playlist_change_details(playlist_id=Spotify.get_playlist("BB-Genre-.*").id, name="BB-Genre-%s" % todays_genre.title())

def makeplaylists():
    today = datetime.date.today()

    todays_songs = [song for song in get_todays_songs() if song[2]][:100]

    chosen_songs = []
    random.seed(today.strftime("%Y-%m-%d"))
    chosen_songs.extend(random.sample(todays_songs[:30], 10))
    chosen_songs.extend(random.sample(todays_songs[30:60], 10))
    chosen_songs.extend(random.sample(todays_songs[60:80], 10))
    chosen_songs.extend(random.sample(todays_songs[80:100], 10))
    chosen_songs = sorted(chosen_songs, key=lambda song: song[3], reverse=True)
    chosen_songs = [uri for *_, uri, _ in chosen_songs]

    # All top ten
    Spotify.get_playlist("BB-Top40").set_tracks(chosen_songs)

    debuts_csv = path.join(dirpath, "./py/data/songdebuts.csv")
    debuts = {(title, artist): None for title, artist, *_ in todays_songs}
    with open(debuts_csv, "r") as debuts_infile:
        debuts_reader = csv.reader(debuts_infile)
        next(debuts_reader)
        for *title_artist, debut in debuts_reader:
            title_artist = tuple(title_artist)
            if title_artist in debuts:
                debuts[title_artist] = datetime.date.fromisoformat(debut)
    todays_songs = sorted(todays_songs, key=lambda song: debuts[(song[0], song[1])])
    Spotify.get_playlist("BB-Hot100").set_tracks([uri for *_, uri, _ in todays_songs])

    make_genre_playlist()

if __name__ == "__main__":
    makeplaylists()
