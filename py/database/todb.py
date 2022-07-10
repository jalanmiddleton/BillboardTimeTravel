'''
TODO: Copied and pasted out of scrape, so likely broken.
'''

def add_bb_entry(item_type, items, day, chart):
    for i, item in enumerate(items):
        id = get_and_add_id(item_type, item["title"], item["artist"])
        insert("INSERT IGNORE INTO billboard.`%s` (week, idx, item_id) \
		       VALUES ('%s', %s, %s)" % (chart, format_date(day), i + 1, id))

def get_and_add_id(item_type, title, artist):
    select_id = "SELECT id, bb_title, bb_artist, spoffy_title, spoffy_artist \
    	from {item_type}s where bb_title = {title}s and bb_artist {artist}s".format(
            item_type=item_type,
            title=sql_prep(title),
            artist=("=" + sql_prep(artist)) if artist is not None else " is NULL"
        )
    id = select(select_id)

    # Add this item if it's not here already.
    if not id:
        item = search_item(item_type, title, artist)

        # Add its associated album too
        # uri not in details means it wasn't found in search
        # tracks and singles shouldn't be added to the albums
        if item_type == "track" and "uri" in item.details and item.album_type != "single":
            album_item = SpotifyItem("album", title, artist, uri=item.album_uri)
            item.details["album_id"] = \
                get_and_add_id("album", album_item.details["spoffy_title"],
                               album_item.details["spoffy_artist"])

        insert("INSERT IGNORE INTO %ss (%s) VALUES (%s)" % \
               (item_type, item.get_keys(), item.get_values()))
        id = select(select_id)

    return id[0][0]


def sql_prep(s):
    return "\"%s\"" % MySQLdb.escape_string(s).decode("utf8") if isinstance(s, str) \
           else str(s)