import unittest
from pyrules2.prolog import var, atom, pairs, rule, RuleBook
from itertools import combinations, product, chain
'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''

class Family(RuleBook):
    @pairs(product([atom.frederik, atom.mary], 
                   [atom.christian, atom.isabella, 
                    atom.vincent, atom.josephine]))
    def children(self, parent, child):
        pass

    @pairs(chain(combinations([atom.frederik, atom.mary], 2),
                 combinations([atom.joachim, atom.marie], 2)))
    def spouse(self, x, y):
        pass

    @pairs(combinations([atom.frederik, atom.joachim], 2))
    def sibling(self, x, y):
        pass

    @rule
    def aunt(self, aunt, niece):
        return (self.children(var.x, niece) & 
               (self.sibling(aunt, var.x) |
                (self.spouse(aunt, var.y) & self.sibling(var.y, var.x))))

class Test(unittest.TestCase):
    def test_foo(self):
        for (aunt, niece) in Family().aunt(var.x, var.y):
            print '{} is aunt/uncle to {}'.format(aunt, niece)
            
if __name__ == "__main__":
    unittest.main()