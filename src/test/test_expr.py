import unittest
from pyrules2.expression import ConstantExpression, AndExpression, OrExpression, when


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
        s = [ConstantExpression({letter: index}) for index, letter in enumerate('abcdef')]
        o = OrExpression(*s)
        r = list(o.all_dicts())
        for index, letter in enumerate('abcdef'):
            self.assertIn({letter: index}, r)
        self.assertEqual(6, len(r))
        # Same dict twice
        o = OrExpression(ConstantExpression({'a': 0}), ConstantExpression({'a': 0}))
        self.assertEqual([{'a': 0}, {'a': 0}], list(o.all_dicts()))
        # dicts with same key but different value
        o = OrExpression(ConstantExpression({'a': 0}),
                         ConstantExpression({'a': 1}))
        r = list(o.all_dicts())
        self.assertIn({'a': 0}, r)
        self.assertIn({'a': 1}, r)
        self.assertEqual(2, len(r))
        # OR subexpression
        o = OrExpression(OrExpression(), OrExpression(ConstantExpression(dict())))
        self.assertEqual([dict()], list(o.all_dicts()))
        # Argument is not an Expression
        self.assertRaises(Exception, OrExpression, 42)
        self.assertRaises(Exception, OrExpression, {'a': 'b'})
        # Repeated invocations
        o = OrExpression(ConstantExpression({'a': 'b'}))
        self.assertListEqual([{'a': 'b'}], list(o.all_dicts()))
        self.assertListEqual([{'a': 'b'}], list(o.all_dicts()))

    def test_and(self):
        # 0 subexpressions
        o = AndExpression()
        self.assertListEqual([], list(o.all_dicts()))
        # 1 subexpression
        o = AndExpression(ConstantExpression({'a': 'b'}))
        self.assertListEqual([{'a': 'b'}], list(o.all_dicts()))
        # 2 subexpressions, independent
        o = AndExpression(ConstantExpression({'a': 0}),
                          ConstantExpression({'b': 1}))
        self.assertListEqual([{'a': 0, 'b': 1}], list(o.all_dicts()))
        # >2 subexpressions, independent
        s = [ConstantExpression({letter: index}) for index, letter in enumerate('abcdef')]
        o = AndExpression(*s)
        r = list(o.all_dicts())
        self.assertEqual(1, len(r))
        d = r[0]
        for index, letter in enumerate('abcdef'):
            self.assertEquals(index, d[letter])
        self.assertEqual(6, len(d))
        # Same dict twice
        o = AndExpression(ConstantExpression({'a': 0}), ConstantExpression({'a': 0}))
        self.assertEqual([{'a': 0}], list(o.all_dicts()))
        # dicts with same key but different value
        o = AndExpression(ConstantExpression({'a': 0, 'b': 1}),
                          ConstantExpression({'a': 1, 'b': 1}))
        self.assertListEqual([], list(o.all_dicts()))
        # AND subexpression, 1 empty
        o = AndExpression(AndExpression(), AndExpression(ConstantExpression(dict())))
        self.assertEqual([], list(o.all_dicts()))
        # AND subexpression
        o = AndExpression(AndExpression(ConstantExpression(dict())),
                          AndExpression(ConstantExpression(dict())))
        self.assertEqual([dict()], list(o.all_dicts()))
        # Argument is not an Expression
        self.assertRaises(Exception, AndExpression, 42)
        self.assertRaises(Exception, AndExpression, {'a': 'b'})
        # Repeated invocations
        o = AndExpression(ConstantExpression({'a': 'b'}))
        self.assertListEqual([{'a': 'b'}], list(o.all_dicts()))
        self.assertListEqual([{'a': 'b'}], list(o.all_dicts()))

    def test_when(self):
        w = when(a=0, b=1)
        self.assertListEqual([{'a': 0, 'b': 1}], list(w.all_dicts()))

    def test_or_op(self):
        self.assertListEqual([{'a': 0}, {'a': 1}],
                             list((when(a=0) | when(a=1)).all_dicts()))

    def test_and_op(self):
        self.assertListEqual([{'a': 0, 'b': 1}],
                             list((when(a=0) & when(b=1)).all_dicts()))

    def test_and_or(self):
        e = when(a=0) & (when(b=0) | when(b=1))
        self.assertListEqual([{'a': 0, 'b': 0},
                              {'a': 0, 'b': 1}],
                             list(e.all_dicts()))

    def test_dag(self):
        pass  # TODO




if __name__ == "__main__":
    unittest.main()
