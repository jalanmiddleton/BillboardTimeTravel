from bs4 import BeautifulSoup
import os
import pprint
import requests
import spotipy
import spotipy.util as util
import urllib

#15Aug16 API doesn't support delete!!!!!!

def main():
    #create a spotify folder on my own account for these playlists
    #update: spotify folders cannot be created through web API
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user) #TODO: Error uncaught

    #find every available year
    for year in range(1958, 2017): #ends at 2016
        print year
        year_songs = get_years_top_songs_by_week(year)
        make_playlist(sp, user, year, year_songs)
        #TODO: Token expires before end

def get_token(user):
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(user, scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def get_years_top_songs_by_year(year):
    #TODO Some pages have ready-made top songs
    #http://www.billboard.com/charts/year-end/2015/hot-100-songs
    pass

#for every year on billboard
#   for each week of year
#       assign each song a number of points
#   sort by number of points
#   make a new playlist where songs are ordered by significance
def get_years_top_songs_by_week(year):
    year_URL = "http://www.billboard.com/archive/charts/{0}/hot-100".format(year)
    year_page = urllib.urlopen(year_URL).read()
    year_soup = BeautifulSoup(year_page, "html.parser")
    week_links = year_soup.find_all("a")

    all_songs = {}
    for week in week_links:
        destination = week["href"]
        if not destination.endswith("hot-100") or destination.count('/') != 3:
            continue

        try:
            week_songs = get_weeks_top_songs(destination)
        except IOError as ex:
            continue

        for rank in range(0, len(week_songs)):
            score = 100 - rank
            song = week_songs[rank]
            key = song["title"] + " " + song["artist"]

            if key not in all_songs:
                all_songs[key] = song
            all_songs[key]["score"] += score

    ranked_songs = sorted(all_songs.values(), key=lambda x: x["score"], \
        reverse=True)
    return ranked_songs[0:100]

def get_weeks_top_songs(week):
    week_URL = "https://www.billboard.com" + week
    week_page = urllib.urlopen(week_URL)
    week_soup = BeautifulSoup(week_page, "html.parser")
    chart_rows = week_soup.find_all("div", "chart-row__main-display")

    songs = []
    for row in chart_rows:
        song_artist_spotify = extract_song_info(row)
        songs.append(song_artist_spotify)

    return songs

def extract_song_info(row):
    title = row.find(class_ = "chart-row__song").getText().strip()
    artist = row.find(class_ = "chart-row__artist").getText().strip()
    spotify_button = row.find(class_ = "js-spotify-play-full")

    spotify = None
    if (spotify_button is not None):
        spotify = spotify_button["data-href"]

    return { "title":title, "artist":artist, "spotify":spotify, "score":0 }

def make_playlist(sp, user, year, songs):
    playlist = sp.user_playlist_create(user, year)
    id = playlist["id"]

    for song_without_link in [song for song in songs if song["spotify"] is None]:
        song_link = get_song_link(sp, song_without_link["title"], \
            song_without_link["artist"])
        song_without_link["spotify"] = song_link

    uris = [song["spotify"] for song in songs if song["spotify"] is not None]

    sp.user_playlist_add_tracks(user, id, uris)
    print(len(sp.user_playlist_tracks(user, id)["items"]))

def get_song_link(sp, title, artist):
    title_two = " ".join( title.split()[0:2] )
    artist_two = " ".join( artist.split()[0:2] )
    query = title_two + " " + artist_two
    search_results = sp.search(query)

    #TODO: Not good enough at accommodating differences.
    for result in search_results["tracks"]["items"]:
        for artist_result in result["artists"]:
            artist_lower = artist.lower()
            artist_result_lower = artist_result["name"].lower()

            if artist_lower in artist_result_lower \
                    or artist_result_lower in artist_lower:
                return result["uri"]

    print artist + ", " + title
    return None

def delete_main():
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user)
    delete_all_playlists(sp, user)

def delete_all_playlists(sp, user):
    playlists = sp.user_playlists(user)
    for playlist in playlists['items']:
        name = playlist['name']
        if name is not None and name.isdigit() \
                and int(name) in range(1958, 2017):
            delete_playlist(sp, user, playlist['id'])

def delete_playlist(sp, user, playlist):
    rest = "https://api.spotify.com/v1/users/{0}/playlists/{1}/followers" \
        .format(user, playlist)
    response = sp._delete(rest)

def rename_main():
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user)

    playlists = sp.user_playlists(user)
    for playlist in playlists['items']:
        name = playlist['name']
        if name is not None and name == "Rename This!":
            rename_playlist(sp, user, playlist['id'], "Successful Change!")

def rename_playlist(sp, user, playlist, new_name):
    rest = "https://api.spotify.com/v1/users/{0}/playlists/{1}" \
        .format(user, playlist)
    data = {
        "name": new_name
    }

    response = sp._put(rest, payload=data)

if __name__ == "__main__":
    #main()
    rename_main()
