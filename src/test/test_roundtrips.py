import unittest
from pyrules2 import RuleBook, rule, when, anything, place,  driving_roundtrip, RESET, reroute, limit


BASE = place('Erslev, Denmark', milk=RESET)
LARS = place('Snedsted, Denmark', milk=18)
TINA = place('Bedsted Thy, Denmark', milk=20)
LISA = place('Redsted, Denmark', milk=10)
KARL = place('Rakkeby, Denmark', milk=6)
ROUNDTRIP = driving_roundtrip(BASE, LARS, TINA, BASE, LISA, KARL)


class Dairy(RuleBook):
    @rule
    def roundtrip(self, rt=anything):
        return when(rt=ROUNDTRIP) | reroute(self.roundtrip(rt))

    @rule
    def viable(self, rt=anything):
        return limit(milk=30)(self.roundtrip(rt))


class Test(unittest.TestCase):
    def test_balance(self):
        d = Dairy()
        for scenario in d.viable():
            rt = scenario['rt']
            self.assertIn(rt.milk(max), [28, 30])
            self.assertTrue(379000 < rt.distance() < 382000)
            self.assertTrue(5*3600 < rt.duration() < 6*3600)
        self.assertEqual(16, len(list(d.viable())))


if __name__ == "__main__":
    unittest.main()
