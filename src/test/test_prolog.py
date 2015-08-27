import unittest
from pyrules2.prolog import matches, var, atom, pairs, rule, RuleBook
from itertools import permutations, product, chain
'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''

class Family(RuleBook):
    @rule
    def children(self, parent, child):
        return matches(product([atom.frederik, atom.mary], 
                   [atom.christian, atom.isabella, 
                    atom.vincent, atom.josephine]),
        parent, child)

    @pairs(chain(permutations([atom.frederik, atom.mary]),
                 permutations([atom.joachim, atom.marie])))
    def spouse(self, x, y):
        pass

    @pairs(permutations([atom.frederik, atom.joachim]))
    def sibling(self, x, y):
        pass

    @rule
    def aunt(self, aunt, niece):
        x = var.x
        y = var.y
        return (self.children(x, niece) & 
               (self.sibling(aunt, x) |
                (self.spouse(aunt, y) & self.sibling(y, x))))

class Test(unittest.TestCase):
    def test_foo(self):
        for (aunt, niece) in Family().aunt(var.x, var.y):
            print '{} is aunt/uncle to {}'.format(aunt, niece)
            
if __name__ == "__main__":
    unittest.main()
