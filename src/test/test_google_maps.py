from os import environ
import unittest
import googlemaps
from pyrules2.googlemaps import driving_roundtrip

COP = 'Copenhagen, Denmark'
MAD = 'Madrid, Spain'
BER = 'Berlin, Germany'
LIS = 'Lisbon, Portugal'

KM = 1000


class Test(unittest.TestCase):
    def test_roundtrip(self):
        r = driving_roundtrip(self.client, COP, MAD, BER, LIS)
        self.assertGreater(r.distance(), 10000 * KM)  # Bad
        min_dist, itinerary = min(((a.distance(), a.itinerary()) for a in r.alternatives()))
        self.assertLess(min_dist, 6500 * KM)  # Good
        self.assertListEqual([COP, LIS, MAD, BER, COP], itinerary)

    def setUp(self):
        try:
            key = environ['GOOGLE_MAPS_API_KEY']
        except KeyError:
            self.fail('This test requires an API key for Google Maps in the environment variable GOOGLE_MAPS_API_KEY')
        self.client = googlemaps.Client(key=key)


if __name__ == "__main__":
    unittest.main()
