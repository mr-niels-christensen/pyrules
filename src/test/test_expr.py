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
        # Repeated invocations
        c = ConstantExpression({'a': 'b'})
        self.assertListEqual([{'a': 'b'}], list(c.all_dicts()))
        self.assertListEqual([{'a': 'b'}], list(c.all_dicts()))

    def test_or(self):
        # 0 subexpressions
        o = OrExpression()
        self.assertListEqual([], list(o.all_dicts()))
        # 1 subexpression
        o = OrExpression(ConstantExpression({'a': 'b'}))
        self.assertListEqual([{'a': 'b'}], list(o.all_dicts()))
        # 2 subexpressions
        o = OrExpression(ConstantExpression({'a': 0}),
                         ConstantExpression({'b': 1}))
        r = list(o.all_dicts())
        self.assertIn({'a': 0}, r)
        self.assertIn({'b': 1}, r)
        self.assertEqual(2, len(r))
        # >2 subexpressions
        # Same dict twice
        # dicts with same key but different value
        # OR subexpression
        # Argument is not an Expression
        # Repeated invocations

    def test_or_op(self):
        pass  # TODO

    def test_and(self):
        pass  # TODO

    def test_and_op(self):
        pass  # TODO

    def test_and_or(self):
        pass  # TODO

    def test_when(self):
        pass  # TODO



if __name__ == "__main__":
    unittest.main()
