'''
Go from a total.json to a uris.json
'''

import json
import traceback

from spotify import Spotify #pylint: disable=import-error

# Assumption: total.json and uris.json are in the same order.
with open("py/data/hot-100/total.json", encoding="utf8") as infile:
    songs = json.loads(infile.read())
with open("py/data/hot-100/uris.json", encoding="utf8") as infile:
    uris = json.loads(infile.read())

alreadyread = len(uris)
for idx, song in enumerate(songs[alreadyread:], alreadyread+1):
    print(idx)
    try:
        uri = Spotify().search("track", song["title"], song["artist"])
        print(uri)
        uris.append(uri.get_details())
    except Exception as exc: #pylint: disable=broad-except
        err = traceback.format_exc().split(", ", 1)[1]
        print(err)
        uris.append({
            "artist": song["artist"],
            "title": song["title"],
            "problem": err,
            "type": "track"
        })

    if idx % 1000 == 0:
        with open("py/data/hot-100/uris.json", "w", encoding="utf8") as outfile:
            outfile.write(json.dumps(uris, indent=2))

with open("py/data/hot-100/uris.json", "w", encoding="utf8") as outfile:
    outfile.write(json.dumps(uris, indent=2))
