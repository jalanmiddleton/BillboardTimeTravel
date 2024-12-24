import unittest

from traitlets import default
from Spotify import Spotify, SpotifyItem, Playlist

class SpotifyTest(unittest.TestCase):
    def test_open_account(self):
        spotify = Spotify.get_instance()
        self.assertIsNotNone(spotify)

    def test_get_default_playlist(self):
        default_playlist = Spotify.get_playlist()
        self.assertIsNotNone(default_playlist)
        self.assertEqual(default_playlist.name, Spotify.DEFAULT_PLAYLIST)

    def test_get_default_playlists(self):
        default_playlists = Spotify.get_playlists()
        self.assertSequenceEqual([p.name for p in default_playlists], [Spotify.DEFAULT_PLAYLIST])

    # def test_search(self):
    #     return self.assertFalse(True)

    # def test_get_query(self):
    #     return self.assertFalse(True)

    # def test_remove_parens(self):
    #     return self.assertFalse(True)

    # def test_has_unique_words(self):
    #     return self.assertFalse(True)

    # def test_lss_match(self):
    #     return self.assertFalse(True)


# class SpotifyItemTest(unittest.TestCase):
#     def test_create(self):
#         return self.AssertFalse(True)


# class PlaylistTest(unittest.TestCase):
#     def test_create(self):
#         return self.assertFalse(True)
    

if __name__ == '__main__':
    unittest.main()