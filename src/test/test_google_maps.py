import unittest
import googlemaps
from pyrules2.googlemaps import driving_roundtrip


class Test(unittest.TestCase):
    def setUp(self):
        # TODO: Sane way to import key
        with open('/Users/nhc/git/pyrules/google-maps-api-key.txt') as f:
            self.key = f.read()

    def test_matrix(self):
        c = googlemaps.Client(key=self.key)
        m = driving_roundtrip(c,
                                'Copenhagen, Denmark',
                                'Madrid, Spain',
                                'Berlin, Germany',
                                'Lisbon, Portugal',
                                )
        print 'Total distance: {} km'.format(m.distance()/1000)


if __name__ == "__main__":
    unittest.main()
