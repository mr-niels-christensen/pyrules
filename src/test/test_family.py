import unittest
from pyrules2 import when, rule, RuleBook, ANYTHING
from pyrules2.rules import FixedPointRuleBook, constant
from itertools import product

'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''


class DanishRoyalFamily(FixedPointRuleBook):
    FRED = MARY = CHRIS = ISA = VINCE = JOSIE = JOE = MARIE = constant

    @rule
    def children(self, parent=ANYTHING, child=ANYTHING):
        return \
            (when(parent=self.FRED) | when(parent=self.MARY)) \
            & \
            (when(child=self.CHRIS) | when(child=self.ISA) | when(child=self.VINCE) | when(child=self.JOSIE))

    @rule
    def spouse(self, x=ANYTHING, y=ANYTHING):
        return when(x=self.FRED, y=self.MARY) | when(x=self.JOE, y=self.MARIE) | self.spouse(y, x)

    @rule
    def sibling(self, x=ANYTHING, y=ANYTHING):
        return when(x=self.FRED, y=self.JOE) | self.sibling(y, x)

    @rule
    def aunt(self, aunt=ANYTHING, niece=ANYTHING, x=ANYTHING, y=ANYTHING):
        return (self.children(x, niece) &
                ((self.sibling(aunt, x) & when(y=42)) |  # TODO: Allow unbound y
                (self.spouse(aunt, y) & self.sibling(y, x))))


class Test(unittest.TestCase):
    def test_cls(self):
        print DanishRoyalFamily

    def test_children(self):
        dicts = DanishRoyalFamily().children()
        expected_pairs = product([DanishRoyalFamily.FRED, DanishRoyalFamily.MARY], [DanishRoyalFamily.CHRIS, DanishRoyalFamily.VINCE, DanishRoyalFamily.ISA, DanishRoyalFamily.JOSIE])
        self.assertSetEqual(
            set((d['parent'], d['child']) for d in dicts),
            set(expected_pairs))

    def test_spouse(self):
        drf = DanishRoyalFamily()
        drf.page_size = 10
        dicts = drf.spouse()
        expected_pairs = [(DanishRoyalFamily.JOE, DanishRoyalFamily.MARIE), (DanishRoyalFamily.MARIE, DanishRoyalFamily.JOE), (DanishRoyalFamily.MARY, DanishRoyalFamily.FRED), (DanishRoyalFamily.FRED, DanishRoyalFamily.MARY)]
        self.assertSetEqual(
            set((d['x'], d['y']) for d in dicts),
            set(expected_pairs))

    def test_sibling(self):
        drf = DanishRoyalFamily()
        drf.page_size = 10
        dicts = drf.sibling()
        expected_pairs = [(DanishRoyalFamily.JOE, DanishRoyalFamily.FRED), (DanishRoyalFamily.FRED, DanishRoyalFamily.JOE)]
        self.assertSetEqual(
            set((d['x'], d['y']) for d in dicts),
            set(expected_pairs))

    def test_aunt(self):
        drf = DanishRoyalFamily()
        dicts = list(drf.aunt())
        expected_pairs = product((DanishRoyalFamily.JOE, DanishRoyalFamily.MARIE), (DanishRoyalFamily.CHRIS, DanishRoyalFamily.ISA, DanishRoyalFamily.VINCE, DanishRoyalFamily.JOSIE))
        self.assertSetEqual(
            set((d['aunt'], d['niece']) for d in dicts),
            set(expected_pairs))

if __name__ == "__main__":
    unittest.main()
