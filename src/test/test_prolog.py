import unittest
from pyrules2.prolog import var, RuleBook

'''Example: Family relations

   In this example, we're deducing family relations from a 
   set of basic facts about marriage and offspring.
'''

class Family(RuleBook):
    def children(self, parent, child):
        pass

    def spouse(self, x, y):
        pass

    def sibling(self, x, y):
        pass

    def aunt(self, aunt, niece):
        return (self.children(var.x, niece) & 
               (self.sibling(aunt, var.x) |
                (self.spouse(aunt, var.y) & self.sibling(var.y, var.x))))

class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_foo(self):
        pass
            
if __name__ == "__main__":
    unittest.main()