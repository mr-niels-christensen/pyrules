import unittest
from pyrules2.expression import ConstantExpression, AndExpression, OrExpression, ReferenceExpression, when, FilterEqExpression, RenameExpression, bind


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

    def test_ref(self):
        # Init
        r = ReferenceExpression()
        # Ref not set
        self.assertRaises(Exception, r.all_dicts)
        # Ref set
        r.set_expression(ConstantExpression({'a': 0}))
        self.assertListEqual([{'a': 0}], list(r.all_dicts()))
        # Ref set again
        r.set_expression(ConstantExpression({'b': 1}))
        self.assertListEqual([{'b': 1}], list(r.all_dicts()))
        # Repeated invocation
        self.assertListEqual([{'b': 1}], list(r.all_dicts()))
        # Ref set to non-Expression
        self.assertRaises(Exception, r.set_expression, dict())
        # Constructor gets argument
        self.assertRaises(Exception, ReferenceExpression, ConstantExpression(dict()))

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

    def test_filter_eq(self):
        # Subexpression not an Expression
        self.assertRaises(Exception, FilterEqExpression, 'x', 0, None)
        # Prepare for rest of the test
        r = ReferenceExpression()
        f = FilterEqExpression('x', 0, r)
        # No keys
        r.set_expression(ConstantExpression(dict()))
        gen = f.all_dicts()
        self.assertRaises(Exception, list, gen)
        # Other key
        r.set_expression(when(y=0))
        gen = f.all_dicts()
        self.assertRaises(Exception, list, gen)
        # Only key and matching
        r.set_expression(when(x=0))
        self.assertListEqual([{'x': 0}], list(f.all_dicts()))
        # Only key and not matching
        r.set_expression(when(x=1))
        self.assertListEqual([], list(f.all_dicts()))
        # More keys, matching
        r.set_expression(when(x=0, y=1))
        self.assertListEqual([{'x': 0, 'y': 1}], list(f.all_dicts()))
        # More keys, not matching
        r.set_expression(when(x=1, y=0))
        self.assertListEqual([], list(f.all_dicts()))
        # Several dicts
        r.set_expression(when(x=0) | when(x=0))
        self.assertListEqual([{'x': 0}] * 2, list(f.all_dicts()))
        r.set_expression(when(x=0) | when(x=1))
        self.assertListEqual([{'x': 0}], list(f.all_dicts()))
        r.set_expression(when(x=1) | when(x=0))
        self.assertListEqual([{'x': 0}], list(f.all_dicts()))
        r.set_expression(when(x=2) | when(x=1))
        self.assertListEqual([], list(f.all_dicts()))

    def test_rename(self):
        # Subexpression not an Expression
        self.assertRaises(Exception, RenameExpression, None)
        # No keys
        r = RenameExpression(when(x=0))
        self.assertListEqual([{}], list(r.all_dicts()))
        # One key
        r = RenameExpression(when(x=0), x='y')
        self.assertListEqual([{'y': 0}], list(r.all_dicts()))
        # Unknown key
        r = RenameExpression(when(x=0), y='z')
        gen = r.all_dicts()
        self.assertRaises(Exception, list, gen)
        # Two keys, different values
        r = RenameExpression(when(x=0, y=1), x='a', y='b')
        self.assertListEqual([{'a': 0, 'b': 1}], list(r.all_dicts()))
        # Two keys, same value
        r = RenameExpression(when(x=0, y=1), x='a', y='a')
        self.assertListEqual([], list(r.all_dicts()))
        r = RenameExpression(when(x=0, y=0), x='a', y='a')
        self.assertListEqual([{'a': 0}], list(r.all_dicts()))
        # Several dicts
        r = RenameExpression(when(x=0) | when(x=1), x='a')
        self.assertListEqual([{'a': 0}, {'a': 1}], list(r.all_dicts()))

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
        c = when(a=0)
        e = c & c & c
        self.assertListEqual([{'a': 0}], list(e.all_dicts()))
        e = c | c | c
        self.assertListEqual([{'a': 0}] * 3, list(e.all_dicts()))

    def test_bind(self):
        # No bindings
        b = bind(when(x=0), {}, {})
        self.assertListEqual([{}], list(b.all_dicts()))
        # Constant-bindings only
        b = bind(when(x=0), {'x': 0}, {})
        self.assertListEqual([{}], list(b.all_dicts()))
        b = bind(when(x=0), {'x': 1}, {})
        self.assertListEqual([], list(b.all_dicts()))
        # Variable-bindings only
        b = bind(when(x=0), {}, {'x': 'a'})
        self.assertListEqual([{'a': 0}], list(b.all_dicts()))
        b = bind(when(x=0, y=1), {}, {'x': 'a', 'y': 'b'})
        self.assertListEqual([{'a': 0, 'b': 1}], list(b.all_dicts()))
        b = bind(when(x=0, y=1), {}, {'x': 'a', 'y': 'a'})
        self.assertListEqual([], list(b.all_dicts()))
        # Mixed bindings
        b = bind(when(x=0), {'x': 0}, {'x': 'a'})
        self.assertListEqual([{'a': 0}], list(b.all_dicts()))
        # Bad expression
        self.assertRaises(Exception, bind, None, {}, {})
        # Bad bindings
        self.assertRaises(Exception, bind, when(x=0), None, {})
        self.assertRaises(Exception, bind, when(x=0), {}, None)
        b = bind(when(x=0), {'a': 0}, {})
        gen = b.all_dicts()
        self.assertRaises(Exception, list, gen)
        b = bind(when(x=0), {}, {'a': 'b'})
        gen = b.all_dicts()
        self.assertRaises(Exception, list, gen)

    def test_call_op(self):
        def f(n=1, _dummy=2):
            for i in range(n):
                yield i
        f_when = when(f=f)
        # Call with zero arguments
        c = f_when(when())
        self.assertRaises(Exception, list, c.all_dicts())
        # Call with one argument
        c = f_when(when(n=1))
        self.assertListEqual([{'n': 0}], list(c.all_dicts()))
        # Call with several arguments
        c = f_when(when(n=1, _dummy=2))
        self.assertRaises(Exception, list, c.all_dicts())
        # Returned generator generates no values
        c = f_when(when(n=0))
        self.assertListEqual([], list(c.all_dicts()))
        # Returned generator generates several values
        c = f_when(when(n=3))
        self.assertListEqual([{'n': 0}, {'n': 1}, {'n': 2}], list(c.all_dicts()))
        # Return value not a generator
        c = when(f=lambda x: x)(when(x=0))
        self.assertListEqual([{'x': 0}], list(c.all_dicts()))
        # Call with composite expressions
        #  - Right-hand side
        c = when(f=f)(when(n=1) | when(n=2))
        l = list(c.all_dicts())
        l.sort(key=lambda d: d['n'])
        self.assertListEqual([{'n': 0}, {'n': 0}, {'n': 1}], l)
        #  - Left-hand side
        c = (when(f=f) | when(f=lambda n: n))(when(n=1))
        l = list(c.all_dicts())
        l.sort(key=lambda d: d['n'])
        self.assertListEqual([{'n': 0}, {'n': 1}], l)
        #  - Both sides
        left = when(f=f) | when(f=lambda n: n+1)
        right = when(n=0) | when(n=1)
        c = left(right)
        l = list(c.all_dicts())
        l.sort(key=lambda d: d['n'])
        self.assertListEqual([{'n': 0}, {'n': 1}, {'n': 2}], l)
        # Fail if wrong number of args
        self.assertRaises(Exception, when(f=f), when(n=1), when(n=1))
        # Fail if callee not callable
        self.assertRaises(Exception, when(f=0), when(n=1))
        # Fail if input is not Expression
        self.assertRaises(Exception, when(f=f), 1)


if __name__ == "__main__":
    unittest.main()
