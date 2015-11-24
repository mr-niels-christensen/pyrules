import unittest
import googlemaps
from pyrules2.googlemaps import driving_roundtrip

COP = 'Copenhagen, Denmark'
MAD = 'Madrid, Spain'
BER = 'Berlin, Germany'
LIS = 'Lisbon, Portugal'

KM = 1000


class Test(unittest.TestCase):
    def setUp(self):
        # TODO: Sane way to import key
        with open('/Users/nhc/git/pyrules/google-maps-api-key.txt') as f:
            self.key = f.read()

    def test_roundtrip(self):
        c = googlemaps.Client(key=self.key)
        r = driving_roundtrip(c, COP, MAD, BER, LIS)
        self.assertGreater(r.distance(), 10000 * KM)  # Bad
        min_dist, best_itinerary = min(((a.distance(), a.itinerary()) for a in r.alternatives()))
        self.assertLess(min_dist, 6500 * KM)  # Good
        self.assertListEqual([COP, LIS, MAD, BER, COP], best_itinerary)


if __name__ == "__main__":
    unittest.main()
