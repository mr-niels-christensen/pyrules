import unittest
from pyrules2 import when, rule, RuleBook, ANYTHING, constant
from itertools import product

'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''


class DanishRoyalFamily(RuleBook):
    FRED = MARY = CHRIS = ISA = VINCE = JOSIE = JOE = MARIE = constant

    @rule
    def child(self, parent=ANYTHING, child=ANYTHING):
        p = when(parent=self.FRED) | when(parent=self.MARY)
        c = when(child=self.CHRIS) | when(child=self.ISA) | when(child=self.VINCE) | when(child=self.JOSIE)
        return p & c

    @rule
    def spouse(self, x=ANYTHING, y=ANYTHING):
        return when(x=self.FRED, y=self.MARY) | when(x=self.JOE, y=self.MARIE) | self.spouse(y, x)

    @rule
    def sibling(self, x=ANYTHING, y=ANYTHING):
        return when(x=self.FRED, y=self.JOE) | self.sibling(y, x)

    @rule
    def aunt_uncle(self,
                   aunt_uncle=ANYTHING,
                   niece_nephew=ANYTHING,
                   parent=ANYTHING,
                   spouse=ANYTHING):
        direct = self.sibling(aunt_uncle, parent) & when(spouse=42)
        indirect = self.spouse(aunt_uncle, spouse) & self.sibling(spouse, parent)
        return self.child(parent, niece_nephew) & \
               (direct | indirect)


class Test(unittest.TestCase):
    def test_cls(self):
        print DanishRoyalFamily

    def test_child(self):
        dicts = DanishRoyalFamily().child()
        expected_pairs = product([DanishRoyalFamily.FRED, DanishRoyalFamily.MARY], [DanishRoyalFamily.CHRIS, DanishRoyalFamily.VINCE, DanishRoyalFamily.ISA, DanishRoyalFamily.JOSIE])
        self.assertSetEqual(
            set((d['parent'], d['child']) for d in dicts),
            set(expected_pairs))

    def test_spouse(self):
        drf = DanishRoyalFamily()
        dicts = drf.spouse()
        expected_pairs = [(DanishRoyalFamily.JOE, DanishRoyalFamily.MARIE), (DanishRoyalFamily.MARIE, DanishRoyalFamily.JOE), (DanishRoyalFamily.MARY, DanishRoyalFamily.FRED), (DanishRoyalFamily.FRED, DanishRoyalFamily.MARY)]
        self.assertSetEqual(
            set((d['x'], d['y']) for d in dicts),
            set(expected_pairs))

    def test_sibling(self):
        drf = DanishRoyalFamily()
        dicts = drf.sibling()
        expected_pairs = [(DanishRoyalFamily.JOE, DanishRoyalFamily.FRED), (DanishRoyalFamily.FRED, DanishRoyalFamily.JOE)]
        self.assertSetEqual(
            set((d['x'], d['y']) for d in dicts),
            set(expected_pairs))

    def test_aunt(self):
        drf = DanishRoyalFamily()
        dicts = list(drf.aunt_uncle())
        expected_pairs = product((DanishRoyalFamily.JOE, DanishRoyalFamily.MARIE), (DanishRoyalFamily.CHRIS, DanishRoyalFamily.ISA, DanishRoyalFamily.VINCE, DanishRoyalFamily.JOSIE))
        self.assertSetEqual(
            set((d['aunt_uncle'], d['niece_nephew']) for d in dicts),
            set(expected_pairs))

if __name__ == "__main__":
    unittest.main()
