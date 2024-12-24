'''
Some quick tests to know when things fall apart.
'''
# pylint: skip-file

from datetime import datetime
from unittest import TestCase, main

from scrape import scrape_chart
from spotify import Spotify, SpotifyItem

class TestScrape(TestCase):
    def test_scrape_hot100_7jan1984_50(self):
        '''
        The 50th song on January 7th, 1984 is 99 Luftballons by Nena.
        https://www.billboard.com/charts/hot-100/1984-01-07?rank=50
        '''
        chart = scrape_chart("hot-100", datetime(1984, 1, 7))
        self.assertEqual(len(chart), 100)
        self.assertEqual(chart[49], {"title": "99 Luftballons", "artist": "Nena"})

    def test_scrape_billboard200_24jul1976_50(self):
        '''
        The 50th album on July 24, 1976 is Fever by Ronnie Laws.
        https://www.billboard.com/charts/billboard-200/1976-07-24?rank=50
        '''
        chart = scrape_chart("billboard-200", datetime(1976, 7, 24))
        self.assertEqual(len(chart), 200)
        self.assertEqual(chart[49], {"title": "Fever", "artist": "Ronnie Laws"})

    def test_spotifyitem_rickroll(self):
        '''
        Can I get Never Gonna Give You Up?
        TODO: Setting Popularity at 80 is not futureproofed.
        '''
        rick = Spotify.search("track", "Never Gonna Give You Up", "Rick Astley").get_details()
        expected = {
            'artist': 'Rick Astley',
            'artist_spotify': 'Rick Astley',
            'duration': 213573,
            'popularity': 80,
            'problem': None,
            'title': 'Never Gonna Give You Up',
            'title_spotify': 'Never Gonna Give You Up',
            'type': 'track',
            'uri': 'spotify:track:4cOdK2wGLETKBW3PvgPWqT'
        }
        self.assertEqual(rick, expected)

    def test_spotifyitem_pearljam(self):
        '''
        Can I get Ten?
        '''
        pj = Spotify.search("album", "Ten", "Pearl Jam").get_details()
        expected = {
            'artist': 'Pearl Jam',
            'artist_spotify': 'Pearl Jam',
            'duration': -1,
            'popularity': None,
            'problem': None,
            'title': 'Ten',
            'title_spotify': 'Ten',
            'type': 'album',
            'uri': 'spotify:album:5B4PYA7wNN4WdEXdIJu58a'
        }
        self.assertEqual(pj, expected)


if __name__ == '__main__':
    main()