import unittest
from pyrules2 import when, rule, RuleBook, ANYTHING
from pyrules2.pedia import pedia, Pedia
from pyrules2.expression import load

'''Example:

'''


class World(RuleBook):
    @rule
    def children(self, parent=ANYTHING, child=ANYTHING):
        return load(parent, child) << pedia('children')

    @rule
    def grandchild(self, x=ANYTHING, z=ANYTHING, y=ANYTHING):
        return self.children(x, y) & self.children(y, z)


class Test(unittest.TestCase):
    def test_cls(self):
        print World

    def test_world(self):
        w = World()
        w.page_size = 10
        l = list(w.children())
        print l
        #self.assertIn({'x': Pedia('Abd_Manaf_ibn_Qusai'), 'z': Pedia('Umayya_ibn_Abd_Shams')}, l)

if __name__ == "__main__":
    unittest.main()
