import unittest
import googlemaps
from pyrules2.googlemaps import GoogleMapsMatrix


class Test(unittest.TestCase):
    def setUp(self):
        # TODO: Sane way to import key
        with open('/Users/nhc/git/pyrules/google-maps-api-key.txt') as f:
            self.key = f.read()

    def test_matrix(self):
        c = googlemaps.Client(key=self.key)
        m = GoogleMapsMatrix(c,
                             'Aboyne, Scotland',
                             'Peterhead, Scotland',
                             'Inverurie, Scotland')
        print m


if __name__ == "__main__":
    unittest.main()
