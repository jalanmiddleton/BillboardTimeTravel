import unittest

from traitlets import default
from Spotify import Spotify, SpotifyItem, Playlist

class SpotifyTest(unittest.TestCase):
    def test_open_account(self):
        spotify = Spotify._get_instance()
        self.assertIsNotNone(spotify)

    def test_get_default_playlist(self):
        default_playlist = Spotify.get_playlist()
        self.assertIsNotNone(default_playlist)
        self.assertEqual(default_playlist.name, Spotify.DEFAULT_PLAYLIST)

    def test_get_default_playlists(self):
        default_playlists = Spotify.get_playlists()
        self.assertSequenceEqual([p.name for p in default_playlists], [Spotify.DEFAULT_PLAYLIST])

    # def test_search(self):
    #     title = "Never Gonna Give You Up"
    #     artist = "Rick Astley"
    #     uri = Spotify.search(title, artist).uri
    #     self.assertEqual(uri, "")


# class SpotifyItemTest(unittest.TestCase):
#     def test_create(self):
#         return self.AssertFalse(True)


# class PlaylistTest(unittest.TestCase):
#     def test_create(self):
#         return self.assertFalse(True)
    

if __name__ == '__main__':
    unittest.main()