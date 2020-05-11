from BBtoDB import scrape
import datetime

today = datetime.date.today()
aweekago = today - datetime.timedelta(days=7)

scrape(today, aweekago)
