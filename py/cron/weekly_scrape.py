'''
TODO: Likely broken after directory move.
'''

from datetime import date, timedelta

from scrape import scrape #pylint:disable=import-error

today = date.today()
recentsaturday = today - timedelta((today.weekday() + 2) % 7)
aweekago = recentsaturday - timedelta(days=7)
scrape(recentsaturday, aweekago)
