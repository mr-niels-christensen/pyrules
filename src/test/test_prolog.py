import unittest
from pyrules2.prolog import var, atom, pairs, rule, RuleBook
from itertools import permutations, product, chain
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

    @pairs(chain(permutations([atom.frederik, atom.mary]),
                 permutations([atom.joachim, atom.marie])))
    def spouse(self, x, y):
        pass

    @pairs(permutations([atom.frederik, atom.joachim]))
    def sibling(self, x, y):
        pass

    @rule
    def aunt(self, aunt, niece):
        return (self.children(var.x, niece) & 
               (self.sibling(aunt, var.x) |
                (self.spouse(aunt, var.y) & self.sibling(var.y, var.x))))

class Test(unittest.TestCase):
    def test_foo(self):
        #TODO for (aunt, niece) in Family().aunt(var.x, var.y):
        for d in Family().aunt(var.A, var.B):
            print d#'{} is aunt/uncle to {}'.format(aunt, niece)
            
if __name__ == "__main__":
    unittest.main()
