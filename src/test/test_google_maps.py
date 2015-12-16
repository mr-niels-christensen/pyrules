import unittest
from pyrules2.googlemaps import driving_roundtrip, place

COP = place('Copenhagen, Denmark')
MAD = place('Madrid, Spain')
BER = place('Berlin, Germany')
LIS = place('Lisbon, Portugal')

KM = 1000


class Test(unittest.TestCase):
    def test_roundtrip(self):
        r = driving_roundtrip(COP, MAD, BER, LIS)
        self.assertGreater(r.distance, 10000 * KM)  # Bad
        min_dist, itinerary = min(((a.distance, a.places) for a in r.alternatives()))
        self.assertLess(min_dist, 6500 * KM)  # Good
        self.assertListEqual([COP, LIS, MAD, BER, COP], list(itinerary))


if __name__ == "__main__":
    unittest.main()
