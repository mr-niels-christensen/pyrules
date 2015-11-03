import unittest
from pyrules2 import when, rule, RuleBook, ANYTHING
from itertools import product, islice

'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''

FRED, MARY, CHRIS, ISA, VINCE, JOSIE, JOE, MARIE = range(8)


class DanishRoyalFamily(RuleBook):
    @rule
    def children(self, parent=ANYTHING, child=ANYTHING):
        return \
            (when(parent=FRED) | when(parent=MARY)) \
            & \
            (when(child=CHRIS) | when(child=ISA) | when(child=VINCE) | when(child=JOSIE))

    @rule
    def spouse(self, x=ANYTHING, y=ANYTHING):
        return when(x=FRED, y=MARY) | when(x=JOE, y=MARIE) | self.spouse(y, x)

    @rule
    def sibling(self, x=ANYTHING, y=ANYTHING):
        return when(x=FRED, y=JOE) | self.sibling(y, x)

    @rule
    def aunt(self, aunt=ANYTHING, niece=ANYTHING, x=ANYTHING, y=ANYTHING):
        return (self.children(x, niece) &
                ((self.sibling(aunt, x) & when(y=ANYTHING)) |  # TODO: Allow unbound y
                (self.spouse(aunt, y) & self.sibling(y, x))))


class Test(unittest.TestCase):
    def test_cls(self):
        print DanishRoyalFamily

    def test_children(self):
        dicts = DanishRoyalFamily().children().all_dicts()
        expected_pairs = product([FRED, MARY], [CHRIS, VINCE, ISA, JOSIE])
        self.assertSetEqual(
            set((d['parent'], d['child']) for d in dicts),
            set(expected_pairs))

    def test_spouse(self):
        dicts = islice(DanishRoyalFamily().spouse().all_dicts(), 10)
        expected_pairs = [(JOE, MARIE), (MARIE, JOE), (MARY, FRED), (FRED, MARY)]
        self.assertSetEqual(
            set((d['x'], d['y']) for d in dicts),
            set(expected_pairs))

    def test_sibling(self):
        dicts = islice(DanishRoyalFamily().sibling().all_dicts(), 10)
        expected_pairs = [(JOE, FRED), (FRED, JOE)]
        self.assertSetEqual(
            set((d['x'], d['y']) for d in dicts),
            set(expected_pairs))

    def test_aunt(self):
        dicts = list(islice(DanishRoyalFamily().aunt().all_dicts(), 10))
        expected_pairs = product((JOE, MARIE), (CHRIS, ISA, VINCE, JOSIE))
        self.assertSetEqual(
            set((d['aunt'], d['niece']) for d in dicts),
            set(expected_pairs))

if __name__ == "__main__":
    unittest.main()
