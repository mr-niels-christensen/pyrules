import unittest
from pyrules2.expression import ConstantExpression, AndExpression, OrExpression


class Test(unittest.TestCase):
    def test_constant(self):
        # Empty dict
        c = ConstantExpression(dict())
        self.assertListEqual([dict()], list(c.all_dicts()))
        # dict with one item
        c = ConstantExpression({'a': 'b'})
        self.assertListEqual([{'a': 'b'}], list(c.all_dicts()))
        # dict with two items
        c = ConstantExpression({'a': 0, 'b': 1})
        self.assertListEqual([{'a': 0, 'b': 1}], list(c.all_dicts()))
        # Missing dict
        self.assertRaises(Exception, ConstantExpression)
        # Two dicts
        self.assertRaises(Exception, ConstantExpression, dict(), dict())
        # Not a dict
        self.assertRaises(Exception, ConstantExpression, 0)
        # Modifying the dict should not affect the Expression
        d = {'a': 0}
        c = ConstantExpression(d)
        d['a'] = 1
        self.assertListEqual([{'a': 0}], list(c.all_dicts()))


if __name__ == "__main__":
    unittest.main()
