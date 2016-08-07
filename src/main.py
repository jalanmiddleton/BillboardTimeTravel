from bs4 import BeautifulSoup
import spotipy
import spotipy.util as util
import urllib

def main():
    #create a spotify folder on my own account for these playlists
    #update: spotify folders cannot be created through web API
    sp = get_token()

    #find every available year
    for year in range(1958, 2017): #ends at 2016
        year_songs = get_years_top_songs(year)

    iterate_years()

    print "in main"

def get_token():
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token("1246540326", scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

#for every year on billboard
#   for each week of year
#       assign each song a number of points
#   sort by number of points
#   make a new playlist where songs are ordered by significance
def get_years_top_songs(year):
    year_URL = "http://www.billboard.com/archive/charts/{0}/hot-100".format(year)
    year_page = urllib.urlopen(year_URL).read()
    year_soup = BeautifulSoup(year_page, "html.parser")
    week_links = year_soup.find_all("a")

    for week in week_links:
        destination = week["href"]
        if not destination.endswith("hot-100") or destination.count('/') != 3:
            continue

        try:
            week_songs = get_weeks_top_songs(destination)
        except IOError as ex:
            continue

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

    return (title, artist, spotify)

if __name__ == "__main__":
    print "Main program!"
    main()
