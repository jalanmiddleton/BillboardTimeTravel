'''
Scrape billboard.come, week-by-week.
Put the information into a database or json file.
Used to be DB, but JSON is more portable.
'''

import json
import os
import traceback

from urllib.request import urlopen, Request
from datetime import datetime, timedelta

from bs4 import BeautifulSoup


def scrape(chart, start=datetime(2022, 7, 9), end=datetime(1958, 1, 1)):
    '''
    Iterate week by week and scrape each page.
    start: first day to scrape
    end: last day to scrape, inclusive
    '''
    # Start at the most recent saturday. (which is weekday = 5)
    day = start - timedelta((start.weekday() + 2) % 7)

    while day >= end:
        try:
            filename = f"./py/data/{chart}/{day.year}/{day.month}-{day.day}.json"
            if not os.path.exists(filename):
                charts = scrape_chart(chart, day)
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, "w", encoding="utf-8") as outfile:
                    outfile.write(json.dumps(charts, indent=2))
        except Exception: #pylint: disable=broad-except
            with open("./py/data/errors.txt", "a", encoding="utf-8") as errorfile:
                print("Writing to error file...")
                errorfile.write("For " + str(day) + "...\n")
                traceback.print_exc(file=errorfile)
                errorfile.write("\n\n")
            break

        day -= timedelta(7)

    consolidate(chart)

def scrape_chart(chart, day):
    '''
    Scrape a chart from billboard.com.
    chart: the chart/URL directory.
    day: the YYYY-MM-DD for the billboard.
    '''
    day_fmt = f"{day.year}-{str(day.month).zfill(2)}-{str(day.day).zfill(2)}"
    url = f"https://www.billboard.com/charts/{chart}/{day_fmt}"

    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'})) as raw_html:
        songs = scrape_html(raw_html)

    return songs

def scrape_html(html):
    '''
    Valid as of 10 July 2022.
    '''
    page_soup = BeautifulSoup(html, "html.parser")
    songsoup = page_soup.find_all("div", class_="o-chart-results-list-row-container")
    songs = []
    for song in songsoup:
        title_elem = song.find("h3")
        songs.append({
            'title': title_elem.text.strip(),
            'artist': title_elem.find_next().text.strip()
        })
    return songs

def consolidate(chart):
    '''
    Load local json files.
    '''
    path = f"./py/data/{chart}"
    if not os.path.exists(path):
        raise ValueError(f"No data for chart {chart} exists.")

    songs = {}
    for year in os.listdir(path):
        if not year.isdecimal():
            continue

        # weekpath will have ".json" in it, so it's not quite just the week.
        for weekpath in os.listdir(f"{path}/{year}"):
            with open(f"{path}/{year}/{weekpath}", encoding="utf8") as songfile:
                weeksongs = json.loads(songfile.read())
            week = weekpath.split(".")[0]
            for idx, song in enumerate(weeksongs, 1):
                key = f"{song['title']} BY {song['artist']}"
                if key not in songs:
                    song["weeks"] = [{
                        "week": f"{year}-{week}",
                        "position": idx
                    }]
                    songs[key] = song
                else:
                    songs[key]["weeks"].append({
                        "week": f"{year}-{week}",
                        "position": idx
                    })

    with open(f"./py/data/{chart}/total.json", "w", encoding="utf8") as outfile:
        outfile.write(json.dumps(list(songs.values()), indent=2))

if __name__ == "__main__":
    # Charts: "hot-100", "billboard-200"
    scrape("hot-100")
