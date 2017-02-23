from bs4 import BeautifulSoup
import math
import os
import pprint
import requests
import spotipy
import spotipy.util as util
import sys
import urllib

#15Aug16 API doesn't support delete!!!!!!

#TODO: I don't want default to be all years.
def main(years=range(1958, 2018), replace=False, debug=False):
    if isinstance(years, int):
        if years < 1958 or years > 2017:
            print "Year {} beyond available data.".format(years)
            return
        years = [years]
    elif not isinstance(years, list):
        print "Bad format for years."
        return

    #create a spotify folder on my own account for these playlists
    #update: spotify folders cannot be created through web API
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user) #TODO: Error uncaught

    if debug:
        debugging_whatever(sp, user)
        return

    #find every available year
    for year in years: #ends at 2016
        print "Making list for", year

        year_songs = get_years_top_songs_by_year(year)
        if year_songs is None:
            year_songs = get_years_top_songs_by_week(year)

        if replace:
            replace_playlist(sp, user, "BB", year, year_songs)
        else:
            make_playlist(sp, user, "BB", year, year_songs)

        make_grammy_playlist(sp, user, year)
        #TODO: Token might expire for a long list before end

def get_token(user):
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(user, scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def get_years_top_songs_by_year(year):
    #http://www.billboard.com/charts/year-end/2015/hot-100-songs
    if year not in range(2006, 2017): #manaully determined
        return None

    year_url = "http://www.billboard.com/charts/year-end/{}/hot-100-songs" \
        .format(year)
    songs = get_songs_from_page(year_url)

    return songs

#for every year on billboard
#   for each week of year
#       assign each song a number of points
#   sort by number of points
#   make a new playlist where songs are ordered by significance
def get_years_top_songs_by_week(year):
    year_URL = "http://www.billboard.com/archive/charts/{}/hot-100".format(year)
    year_page = urllib.urlopen(year_URL).read()
    year_soup = BeautifulSoup(year_page, "html.parser")
    week_links = year_soup.find_all("a")

    all_songs = {}
    for week in week_links:
        #https://www.billboard.com/charts/1958-08-09/hot-100
        destination = "https://www.billboard.com" + week["href"]
        if not destination.endswith("hot-100") or destination.count('/') != 5:
            continue

        try:
            week_songs = get_songs_from_page(destination)
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
    return ranked_songs[:100]

def get_songs_from_page(page):
    page_html = urllib.urlopen(page)
    page_soup = BeautifulSoup(page_html, "html.parser")
    chart_rows = page_soup.find_all("div", "chart-row__main-display")

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

def replace_playlist(sp, user, prefix, year, songs, partitions=6):
    all_playlists = sp.user_playlists(user)["items"]
    relevant_playlists = []
    offset_now = 50
    while len(all_playlists) > 0:
        relevant_playlists += [playlist for playlist in all_playlists \
            if playlist["name"].startswith(prefix + "-")]
        all_playlists = sp.user_playlists(user, offset=offset_now)["items"]
        offset_now += 50

    if not relevant_playlists:
        make_playlist(sp, user, prefix, year, songs, partitions)
    else:
        if len(relevant_playlists) != partitions:
            raise IOError("Unexpected number of playlists: " + str(len(relevant_playlists)))

        relevant_playlists.sort(key = lambda x : x["name"])
        uris = get_good_uris(sp, songs)
        playlist_len = int(math.ceil(len(uris) / float(partitions)))

        for idx, playlist in enumerate(relevant_playlists):
            start = idx*playlist_len
            sp.user_playlist_replace_tracks(user, playlist["id"], uris[start:start+playlist_len])

            oldname = playlist["name"]
            newname = oldname.split(":")[0] + ": " + year
            rename_playlist(sp, user, playlist["id"], newname)

def make_playlist(sp, user, prefix, year, songs, partitions=6):
    uris = get_good_uris(sp, songs)
    playlist_len = int(math.ceil(len(uris) / float(partitions)))
    for i in range(0, len(uris), playlist_len):
        idx = i/playlist_len + 1
        playlist = sp.user_playlist_create(user, "{}-{}: {}".format(prefix, idx, year))
        playlist_id = playlist["id"]
        sp.user_playlist_add_tracks(user, playlist_id, uris[i:i+playlist_len])

    print len(uris), "songs added"

def get_good_uris(sp, songs):
    for song_without_link in [song for song in songs if song["spotify"] is None]:
        song_link = get_song_link(sp, song_without_link["title"], \
            song_without_link["artist"])
        song_without_link["spotify"] = song_link

    uris = [song["spotify"] for song in songs if song["spotify"] is not None]
    uris = map(lambda x : x.split("?")[0], uris)

    return uris

def get_song_link(sp, title, artist):
    title_two = " ".join( title.split()[:2] )
    artist_two = " ".join( artist.split()[:2] )
    query = title_two + " " + artist_two
    search_results = sp.search(query)

    #TODO: Not good enough at accommodating differences.
    #isolated t d or s needs to be connected to previous word
    #featuring is a distraction
    for result in search_results["tracks"]["items"]:
        for artist_result in result["artists"]:
            artist_lower = artist.lower()
            artist_result_lower = artist_result["name"].lower()

            if "tribute" in artist_result_lower or "karaoke" in artist_result_lower:
                continue

            if artist_lower in artist_result_lower \
                    or artist_result_lower in artist_lower:
                return result["uri"]

    print "Missing:", artist, ",", title
    return None

def make_grammy_playlist(sp, user, year):
    songs = get_grammy_songs(sp, year)
    replace_playlist(sp, user, "GRAMMY", year, songs, partitions=1)

def get_grammy_songs(sp, year):
    grammy_url = "https://www.grammy.com/nominees/search?year={}".format(year)
    grammy_html = urllib.urlopen(grammy_url)
    grammy_soup = BeautifulSoup(grammy_html, "html.parser")

    songs = []
    entries = grammy_soup.find_all("tr")
    for entry in entries:
        yearstr = entry.find(class_="views-field-year").getText().strip()
        category = entry.find(class_="views-field-category-code").getText().strip().lower()
        work = entry.find(class_="views-field-field-nominee-work").getText().strip().lower()
        nominee = entry.find(class_="views-field-field-nominee-extended").getText().strip().lower()

        if  yearstr != year or work == "" or "comedy" in category:
            continue

        artists_raw = nominee.split(",")[0]
        all_artists = artists_raw.split("&")
        first_artist = all_artists[0]

        if "album" in category:
            query = work + " " + first_artist
            album_search = sp.search(query, type="album")
            for r in album_search["albums"]["items"]:
                album_name =  r["name"].lower()
                if "tribute" in album_name or "karaoke" in album_name:
                    continue

                album_uri = r["uri"]
                album_songs = sp.album_tracks(album_uri)
                songs[0:0] = [ \
                    {"title":s["name"], "artist":first_artist, "spotify":s["uri"]} \
                    for s in album_songs["items"] \
                ]
                break #want only one
            #add album
        else:
            song_link = get_song_link(sp, work, first_artist)
            if song_link is not None:
                songs.append({ "title": work, "artist": first_artist, "spotify": song_link})
            #add song

    return songs[:100] #max number

def delete_playlist(sp, user, playlist):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}/followers" \
        .format(user, playlist)
    response = sp._delete(rest)

def rename_playlist(sp, user, playlist, new_name):
    rest = "https://api.spotify.com/v1/users/{}/playlists/{}" \
        .format(user, playlist)
    data = {
        "name": new_name
    }

    response = sp._put(rest, payload=data)

def debugging_whatever(sp, user):
    pls = sp.user_playlists(user)
    print pls
    #print [x["name"] for x in ["items"]]
    pass

if __name__ == "__main__":
    years = sys.argv[1:]
    main(years, years)#True)
