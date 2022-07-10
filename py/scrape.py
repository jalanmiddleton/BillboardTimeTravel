'''
Scrape billboard.come, week-by-week.
Put the information into a database or json file.
Used to be DB, but JSON is more portable.
'''

import json
from pprint import pprint
import re
import string
#import sys
#import traceback

from urllib.request import urlopen, Request
from datetime import datetime, timedelta
#from random import shuffle

from bs4 import BeautifulSoup

from Spotify import Spotify #pylint: disable=import-error
from logger import LOG #pylint: disable=import-error

def scrape(start=datetime(2022, 7, 9), end=datetime(1958, 1, 1)):
    '''
    Iterate week by week and scrape each page.
    start: first day to scrape
    end: last day to scrape, inclusive
    '''
    # TODO: set date to previous or current saturday?
    # TODO: figure out the day that it transitioned from some other day to Saturday
    day = start
    while day >= end:
        pprint(scrape_chart("hot-100", day))
        pprint(scrape_chart("billboard-200", day))
        day -= timedelta(7)

def scrape_chart(chart, day):
    '''
    Scrape a chart from billboard.com.
    chart: the chart/URL directory.
    day: the YYYY-MM-DD for the billboard.
    '''
    day_fmt = f"{day.year}-{str(day.month).zfill(2)}-{str(day.day).zfill(2)}"
    url = f"https://www.billboard.com/charts/{chart}/{day_fmt}"
    raw_html = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
    page_soup = BeautifulSoup(raw_html, "html.parser")
    return scrape_soup(page_soup)
    #return [{'title': y['title'], 'artist': y['artist_name']} for y in charts]
    #try:
    #except Exception as error:
        #raise error
        #LOG(e)
        #traceback.print_exc(file=sys.stdout)

def scrape_soup(soup):
    '''
    Valid as of 10 July 2022.
    '''
    songsoup = soup.find_all("div", class_="o-chart-results-list-row-container")
    songs = []
    for song in songsoup:
        title_elem = song.find("h3")
        songs.append({
            'title': title_elem.text.strip(),
            'artist': title_elem.find_next().text.strip()
        })
    return songs

def remove_parens(s): return re.sub(r"\(.+\)|\[.+\]", "", s)


def has_bad_words(original, result, words):
    return any(word in original != word in result for word in words)


def get_query(title, artist):
    artist = " ".join(filter(
        lambda word: "feat" not in word
        and word not in string.punctuation and len(word) > 1,
        artist.lower().split()))

    return remove_parens(title) + " " + " ".join(re.split(r"\s|,", artist)[:3])


def search_item(item_type, title, artist):
    title_bb = title.lower().strip()
    artist_bb = artist.lower().strip() if artist else ""
    query = get_query(title_bb, artist_bb)
    search_results = Spotify.get_instance().search(q=query, type=item_type, limit=50)

    failed = []
    for result in search_results[item_type + "s"]["items"]:
        title_spoffy = remove_parens(result["name"].lower())
        if has_bad_words(title_bb, title_spoffy, ["cover", "karaoke", "remix"]):
            continue

        artist_spoffy = result["artists"][0]["name"].lower()
        if has_bad_words(artist_bb, artist_spoffy, ["tribute", "karaoke"]):
            break

        if (LSSMatch(artist_bb, artist_spoffy) >= .75 or artist_bb == "soundtrack") \
            and LSSMatch(title_spoffy, title_bb) >= .75:
            return SpotifyItem(item_type, title, artist, search_result=result)

        failed.append("\t\"%s\" by %s" % (title_spoffy, result["artists"][0]["name"]))

    LOG("\t\"%s\" not found" % (query))
    for fail in failed[:5]:
        LOG("\t\t", fail)

    return SpotifyItem(item_type, title, artist)


def LSSMatch(one, two):
    shortest, longest = (one, two) if len(one) < len(two) else (two, one)

    if len(shortest) == 0:
        return 0

    matrix = [[0 for i in range(len(shortest) + 1)]
              for j in range(len(longest) + 1)]
    for x in range(1, len(longest) + 1):
        for y in range(1, len(shortest) + 1):
            matrix[x][y] = (matrix[x - 1][y - 1] + 1) \
                if longest[x - 1] == shortest[y - 1] \
                else max(matrix[x - 1][y], matrix[x][y - 1])

    return float(matrix[-1][-1]) / len(shortest)


class SpotifyItem:
    def __init__(self, item_type, title, artist, search_result=None, uri=None):
        self.type = item_type
        self.details = {
            "bb_artist": artist,
            "bb_title": title
        }

        if uri:
            uri_object = Spotify.get_instance().album(uri) if item_type=="album" \
                         else Spotify.get_instance().track(uri)
        elif search_result:
            uri_object = search_result
            if item_type == "track":
                self.album_uri = search_result["album"]["uri"]
                self.album_type = search_result["album"]["album_type"]
        else:
            return

        if item_type == "album":
            duration = sum(track["duration_ms"] for track \
                           in uri_object["tracks"]["items"]) \
                       if "tracks" in uri_object else -1
        else:
            duration = uri_object["duration_ms"]

        self.details.update({
            "uri": uri or uri_object["uri"],
            "spoffy_artist": ",".join(x["name"] for x in uri_object["artists"]),
            "spoffy_title": uri_object["name"],
            "popularity": uri_object["popularity"] if "popularity" in uri_object else None,
            "duration": duration,
            "genres": ",".join(uri_object["genres"]) if "genres" in uri_object else None
        })

    def sql_prep(self, s):
        return s # TODO: Stub

    def get_keys(self):
        return ",".join(x for x in self.details.keys()
                        if self.details[x] is not None)

    # TODO: this should NOT be calling an external function
    def get_values(self):
        return ",".join(self.sql_prep(x) for x in self.details.values() if x is not None)

    def __str__(self):
        return str(self.details)

######################

if __name__ == "__main__":
    scrape()
