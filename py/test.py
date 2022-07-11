'''
Some quick tests to know when things fall apart.
'''
# pylint: skip-file

from datetime import datetime
from unittest import TestCase, main

from scrape import scrape_chart

class TestScrape(TestCase):
    def test_scrape_hot100_7jan1984_50(self):
        '''
        The 50th song on January 7th, 1984 is 99 Luftballons by Nena.
        https://www.billboard.com/charts/hot-100/1984-01-07?rank=50
        '''
        chart = scrape_chart("hot-100", datetime(1984, 1, 7))
        self.assertEqual(len(chart), 100)
        self.assertEqual(chart[49], {"title": "99 Luftballons", "artist": "Nena"})

if __name__ == '__main__':
    main()