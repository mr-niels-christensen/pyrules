import unittest
from pyrules2 import RuleBook, rule, when, anything, place,  driving_roundtrip, RESET, reroute


BASE = place('Erslev, Denmark', milk=RESET)
LARS = place('Snedsted, Denmark', milk=18)
TINA = place('Bedsted Thy, Denmark', milk=20)
LISA = place('Redsted, Denmark', milk=10)
KARL = place('Rakkeby, Denmark', milk=6)
ROUNDTRIP = driving_roundtrip(BASE, LARS, TINA, BASE, LISA, KARL)


class Dairy(RuleBook):
    @rule
    def covers(self, rt=anything):
        return when(rt=ROUNDTRIP) | reroute(self.covers(rt))

    '''@rule
    def viable(self, first_roundtrip=anything, second_roundtrip=anything):
        return self.covers(first_roundtrip, second_roundtrip) & \
               sum('production', first_roundtrip) <= 30 & \
               sum('production', second_roundtrip) <= 30'''


class Test(unittest.TestCase):
    def test_balance(self):
        d = Dairy()
        for scenario in d.covers():
            rt = scenario['rt']
            if rt.milk(max) <= 30:
                print rt.milk(max)
                print '{}km, {}hours'.format(rt.distance()/1000, rt.duration()/3600)
                print [stop['_address_'] for stop in rt.itinerary()]
                print '-'*60


if __name__ == "__main__":
    unittest.main()
