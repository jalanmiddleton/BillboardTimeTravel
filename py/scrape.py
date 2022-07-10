'''
Scrape billboard.come, week-by-week.
Put the information into a database or json file.
Used to be DB, but JSON is more portable.
'''

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
    # TODO: figure out the day that it transitioned from some other day to Saturday

    # Start at the most recent saturday.
    day = start - timedelta((start.weekday() + 2) % 7)

    while day >= end:
        try:
            chart = scrape_chart(chart, day)
        except Exception: #pylint: disable=broad-except
            with open("./py/data/errors.txt", "w+", encoding="utf-8") as errorfile:
                print("Writing to error file...")
                errorfile.write("For " + str(day) + "...\n")
                traceback.print_exc(file=errorfile)

        nextday = day - timedelta(7)
        # TODO: Make JSON directories...
        day = nextday

def scrape_chart(chart, day):
    '''
    Scrape a chart from billboard.com.
    chart: the chart/URL directory.
    day: the YYYY-MM-DD for the billboard.
    '''
    day_fmt = f"{day.year}-{str(day.month).zfill(2)}-{str(day.day).zfill(2)}"
    url = f"https://www.billboard.com/charts/{chart}/{day_fmt}"

    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'})) as raw_html:
        page_soup = BeautifulSoup(raw_html, "html.parser")
        songs = scrape_soup(page_soup)

    return songs

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

if __name__ == "__main__":
    # Charts: "hot-100", "billboard-200"
    scrape("hot-100")
