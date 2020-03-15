import json
import math
import os
import pprint
import re
import string
import sys
import traceback

from urllib.request import urlopen, Request
from datetime import datetime, timedelta
from random import shuffle

import MySQLdb
import requests
from bs4 import BeautifulSoup

from core import _conn, _cur, InitDB, Spotify

INFO = {
	"hot-100": {
		"chart": "hot-100",
		"url": "https://www.billboard.com/charts/hot-100/{}-{}-{}",
		"item_type": "track",
		"popularity": lambda result: result["popularity"]
	},
	"billboard-200": {
		"chart": "billboard-200",
		"url": "https://www.billboard.com/charts/billboard-200/{}-{}-{}",
		"item_type": "album",
		"popularity": lambda result: Spotify().album(result["uri"])["popularity"]
	}
}

def sql_prep(s):
	return "NULL" if s is None else \
		"'%s'" % s.strip().replace("\\", "").replace("\'", "\\\'") \
		if isinstance(s, str) else "%s" % s

class URI:
	def __init__(self, uri=None, artist=None, title=None, popularity=None,
		duration=None):
		self.uri = uri
		self.artist = artist
		self.title = title
		self.popularity = popularity
		self.duration = duration

	def getKeys(self):
		return "uri,popularity,spoffy_title,spoffy_artist" \
			+ (",duration" if self.duration is not None else "")

	# TODO: this should NOT be calling an external function
	def getValues(self):
		return ",".join(map(sql_prep, [self.uri, self.popularity, self.title, \
			self.artist] + \
			([self.duration] if self.duration is not None else [])))

######################

#datetime(2020, 3, 14)
def scrape(day=datetime(2020, 3, 14), end_year=1957):
	global _conn, _cur
	_conn, _cur = InitDB()

	while day.year > end_year:
		try:
			add_items(get_from_page(
				INFO["hot-100"], day), day, INFO["hot-100"])
			add_items(get_from_page(
				INFO["billboard-200"], day), day, INFO["billboard-200"])
			day -= timedelta(7)
		except Exception as e:
			print(e)
			traceback.print_exc(file=sys.stdout)
			continue


def get_from_page(info, day):
	print(day)

	day_url = info["url"].format(day.year, format(
		day.month, '02'), format(day.day, '02'))
	raw_html = urlopen(Request(
		day_url, headers={'User-Agent': 'Mozilla/5.0'}))
	page_soup = BeautifulSoup(raw_html, "html.parser")

	print(day_url)
	return extract_item_info(page_soup)


def extract_item_info(page):
	def html_to_dict(html): return {
		'title': html[0].getText(),
		'artist': html[1].getText()
	}

	x = json.loads(page.find("div", id="charts")['data-charts'])
	items = [{'title': y['title'], 'artist': y['artist_name']} for y in x]
	return items


def add_items(items, day, info):
	global _conn, _cur

	for i, item in enumerate(items):
		select = "SELECT id from %ss where title = %s and artist %s" \
			% (info['item_type'], sql_prep(item['title']),
			"= %s" % sql_prep(item['artist']))
		_cur.execute(select)
		idres = _cur.fetchall()

		if not idres:
			uri = get_item_link(item['title'], item['artist'], info)
			insert = "INSERT IGNORE INTO %ss (title, artist, %s) VALUES \
				(%s, %s, %s)" % \
				(info["item_type"],
				uri.getKeys(),
				sql_prep(item['title']),
				sql_prep(item['artist']),
				uri.getValues())

			_cur.execute(insert)
			_cur.execute(select)
			idres = _cur.fetchall()

		id = idres[0][0]
		week = "{}-{}-{}".format(day.year,
								 format(day.month, "02"), format(day.day, "02"))
		_cur.execute("INSERT IGNORE INTO billboard.`%s` (week, idx, item_id) \
			VALUES ('%s', %s, %s)" % (info["chart"], week, i + 1, id))
		_conn.commit()


def get_item_link(title, artist, info):
	title = title.lower().strip()
	artist = " ".join(filter(
		lambda word: "feat" not in word \
			and word not in string.punctuation and len(word) > 1,
		artist.lower().split())) if artist else ""

	query = re.sub(r"\(.+\)|[.+]", "", title) + \
		" " + " ".join(artist.split()[:3])
	search_results = Spotify().search(
		q=query, type=info["item_type"], limit=50)

	failed = []
	for result in search_results[info["item_type"] + "s"]["items"]:
		item = re.sub(r"\(.+\)|[.+]", "", result["name"].lower())
		if ("cover" not in title and "cover" in item) or \
			("karaoke" not in title and "karaoke" in item) or \
				("remix" not in title and "remix" in item):
			continue

		for artist_result in result["artists"]:
			artist_lower = artist_result["name"].lower()
			if "tribute" in artist_lower or "karaoke" in artist_lower:
				continue

			if (LSSMatch(artist, artist_lower) >= .75 or artist == "soundtrack") \
				and LSSMatch(item, title) >= .75:
				print(result.keys())
				return URI(uri=result["uri"], \
					artist=artist_result["name"], \
					title=result["name"], \
					popularity=info["popularity"](result), \
					duration=result["duration_ms"] if "duration_ms" \
					in result else None)

		failed.append("\"%s\" by %s" % (item, result["artists"][0]["name"]))

	print("\"%s\" not found" % (query))
	for fail in failed[:5]:
		print("\t", fail)

	return URI()


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


def truncate_all():
	global _conn, _cur
	_cur.execute(
		"truncate albums; truncate `billboard-200`; truncate `hot-100`; truncate tracks;")
	_cur.close()
	_cur = _conn._cursor()

def fill_in_uris():
	global _conn, _cur
	_cur.execute("SELECT * FROM songs where id not in (SELECT id FROM uris)")
	for song in _cur.fetchall():
		print(song)

		uri = get_song_link(song[1], song[2])
		if uri:
			newuri = "INSERT IGNORE INTO billboard.uris (id, uri, song, artist) VALUES (%s, '%s', '%s', '%s')" \
				% (song[0], uri["uri"], sql_prep(uri['title']), sql_prep(uri['artist']))
			_cur.execute(newuri)
			_cur.execute("UPDATE billboard.songs SET song='%s', popularity = %s where id = %s"
						% (song[1].replace("'", "\\'"), uri["popularity"], song[0]))
			_conn.commit()

if __name__=="__main__":
	scrape()
