def quiz():
    user = secrets['SPOTIFY_USER']
    sp = get_token(user)
    playlistid, playlist = findplaylist(sp, user, "Quizzable")
    details = [x["track"] for x in playlist["tracks"]["items"]]
    tracks = [{'name': x['name'], 'artist': x['artists']
               [0]['name'], 'uri': x['uri']} for x in details]
    shuffle(tracks)

    sp._put("https://api.spotify.com/v1/me/player/play", payload={
            'uris': [x['uri'] for x in tracks]
            })

    while True:
        song = raw_input("Song? ")
        artist = raw_input("Artist? ")

        _current = sp._get(
            "https://api.spotify.com/v1/me/player/_currently-playing")
        realartist = _current["item"]["artists"][0]["name"]
        realsong = _current["item"]["name"]
        if artist.lower() == realartist.lower() and realsong.lower().startswith(song.lower()):
            remove = raw_input("Nice! Remove? (y/n) ")
            if remove == "y":
                sp.user_playlist_remove_all_oc_currences_of_tracks(
                    user, playlistid, [_current["item"]["uri"]])

            skip = raw_input("Skip? (y/n) ")
            if skip == "y":
                sp._post("https://api.spotify.com/v1/me/player/next")
        else:
            print "booo, it was %s by %s" % (realsong, realartist)
        print
