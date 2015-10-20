import unittest
from pyrules2 import when, rule, RuleBook
from itertools import product, islice

'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''

FRED, MARY, CHRIS, ISA, VINCE, JOSIE, JOE, MARIE = range(8)


class DanishRoyalFamily(RuleBook):
    @rule
    def children(self, parent, child):
        return \
            (when(parent=FRED) | when(parent=MARY)) \
            & \
            (when(child=CHRIS) | when(child=ISA) | when(child=VINCE) | when(child=JOSIE))

    @rule
    def spouse(self, x, y):
        return when(x=FRED, y=MARY) | when(x=JOE, y=MARIE) | self.spouse(y, x)

    @rule
    def sibling(self, x, y):
        return when(x=FRED, y=JOE) | self.sibling(y, x)

    @rule
    def aunt(self, aunt, niece, x=None, y=None):
        return (self.children(x, niece) &
               (self.sibling(aunt, x) |
                (self.spouse(aunt, y) & self.sibling(y, x))))


class Test(unittest.TestCase):
    def test_cls(self):
        print DanishRoyalFamily

    def test_children(self):
        dicts = DanishRoyalFamily().children(None, None).all_dicts()
        expected_pairs = product([FRED, MARY], [CHRIS, VINCE, ISA, JOSIE])
        self.assertSetEqual(
            set((d['parent'], d['child']) for d in dicts),
            set(expected_pairs))

    @unittest.skip('first things first')
    def test_family(self):
        dicts = islice(DanishRoyalFamily().aunt(None, None).all_dicts(), 100)
        expected_pairs = product([JOE, MARIE], [CHRIS, VINCE, ISA, JOSIE])
        self.assertSetEqual(
            set((d['aunt'], d['niece']) for d in dicts),
            set(expected_pairs))

if __name__ == "__main__":
    unittest.main()
