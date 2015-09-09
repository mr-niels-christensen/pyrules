import unittest
from pyrules2 import limit, wikipedia, matches, var, atom, rule, RuleBook
from itertools import islice, permutations, product, chain

'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''

_FRED_MARY_OFFSPRING = [atom.christian, atom.isabella, 
                        atom.vincent, atom.josephine]

class Family(RuleBook):
    @rule
    def children(self, parent, child):
        return matches(
            product([atom.frederik, atom.mary], 
                    _FRED_MARY_OFFSPRING),
            parent, child)

    @rule
    def spouse(self, x, y):
        return matches(
            chain(permutations([atom.frederik, atom.mary]),
                  permutations([atom.joachim, atom.marie])),
            x ,y)

    @rule
    def sibling(self, x, y):
        return matches(
            permutations([atom.frederik, atom.joachim]),
            x, y)

    @rule
    def aunt(self, aunt, niece):
        x = var.x
        y = var.y
        return (self.children(x, niece) & 
               (self.sibling(aunt, x) |
                (self.spouse(aunt, y) & self.sibling(y, x))))

class World(RuleBook):
    @rule
    @limit(200)
    @wikipedia
    def children(self, parent, child):
        pass

    @rule
    def grandchild(self, x, z):
        y = var.y
        return (self.children(x, y) & self.children(y, z))

class Test(unittest.TestCase):
    def test_family(self):
        tuples = (aunt_niece for aunt_niece in Family().aunt(var.x, var.y))
        expected = product([atom.joachim, atom.marie], _FRED_MARY_OFFSPRING)
        self.assertEqual(
            set(tuples),
            set(expected))

    def test_world(self):
        pairs = set(World().grandchild(var.x, var.z))
        self.assertIn((atom.Abd_Manaf_ibn_Qusai, atom.Umayya_ibn_Abd_Shams), pairs)
            
if __name__ == "__main__":
    unittest.main()
