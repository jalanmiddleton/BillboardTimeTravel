'''
TODO: Likely broken after directory move.
'''

from BBtoDB import scrape
from datetime import date, timedelta

today = date.today()

# 0 - 2, 1 - 3, 2 - 4...5 - 0, 6 - 1
recentsaturday = today - timedelta((today.weekday() + 2) % 7)
aweekago = recentsaturday - timedelta(days=7)
scrape(recentsaturday, aweekago)
