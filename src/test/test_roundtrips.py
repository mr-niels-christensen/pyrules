import unittest
from pyrules2 import RuleBook, rule, when, anything, place,  driving_roundtrip, RESET, reroute, leq


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

    @rule
    def viable(self, rt=anything):
        return leq(max, 'milk', 30)(self.covers(rt))


class Test(unittest.TestCase):
    def test_balance(self):
        d = Dairy()
        for scenario in d.viable():
            rt = scenario['rt']
            print rt.milk(max)
            print '{}km, {}hours'.format(rt.distance()/1000, rt.duration()/3600)
            print [stop['_address_'] for stop in rt.itinerary()]
            print '-'*60


if __name__ == "__main__":
    unittest.main()
