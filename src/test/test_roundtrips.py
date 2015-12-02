from os import environ
import unittest
import googlemaps
from pyrules2 import RuleBook, rule, when, anything, place,  driving_roundtrip


BASE = place('Erslev, Denmark')
LARS = place('Snedsted, Denmark', production=18)
TINA = place('Bedsted Thy, Denmark', production=20)
LISA = place('Redsted, Denmark', production=10)
KARL = place('Rakkeby, Denmark', production=6)


class Dairy(RuleBook):
    # ROUTE_A = circular(BASE, LARS, TINA)
    # ROUTE_B = circular(BASE, LISA, KARL)

    @rule
    def covers(self, rt=anything):
        alt = when(f=lambda x: x.alternatives())
        return when(rt=driving_roundtrip(BASE, LARS, TINA, BASE, LISA, KARL)) | \
               alt(self.covers(rt))

    '''@rule
    def viable(self, first_roundtrip=anything, second_roundtrip=anything):
        return self.covers(first_roundtrip, second_roundtrip) & \
               sum('production', first_roundtrip) <= 30 & \
               sum('production', second_roundtrip) <= 30'''


class Test(unittest.TestCase):
    def test_balance(self):
        d = Dairy()
        for scenario in d.covers():
            bad = False
            for p in scenario['rt'].itinerary():
                if p == BASE:
                    load = 0
                else:
                    try:
                        load += p['production']
                    except AttributeError:
                        raise Exception(repr(p))
                if load > 30:
                    bad = True
                    break
            if not bad:
                print scenario['rt'].itinerary()
                print '{}km, {}hours'.format(scenario['rt'].distance()/1000, scenario['rt'].duration()/3600)


if __name__ == "__main__":
    unittest.main()
