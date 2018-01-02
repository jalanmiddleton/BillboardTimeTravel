from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import math
import os
import pprint
import requests
import spotipy
import spotipy.util as util
import string
from nltk.corpus import stopwords
import sys
import urllib

import MySQLdb
conn = MySQLdb.connect(host= "localhost",
                  user="root",
                  passwd=os.environ["MYSQL_PASSWORD"],
                  db="billboard")
cur = conn.cursor()
updatecur = conn.cursor()


#TODO: I don't want default to be all years.
def main():
    user = os.environ['SPOTIFY_USER']
    sp = get_token(user) #TODO: Error uncaught

    cur.execute("SELECT id, uri FROM uris where id > 0;")
    for id, uri in cur:
        if uri is None: continue

        while True:
            try:
                pop = get_popularity(sp, uri)
                q = "UPDATE billboard.songs SET popularity='{}' WHERE id={}".format(pop, id)
                updatecur.execute(q)
                conn.commit()
                break
            except Exception as e:
                print e
                sp = get_token(user)

def get_token(user):
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(user, scope)
    if token:
        return spotipy.Spotify(auth=token)
    else:
        raise RuntimeError("No Spotify token retrieved.")

def get_popularity(sp, uri):
    search_results = sp.track(uri)
    return search_results["popularity"]

if __name__ == "__main__":
    main()
