import unittest
from pyrules.binding import Binding
import pyrules.term 

class Test(unittest.TestCase):
    def test_term(self):
        #is_variable
        self.assertTrue(pyrules.term.is_variable('X'))
        self.assertTrue(pyrules.term.is_variable('Distance'))
        self.assertFalse(pyrules.term.is_variable(' X'))
        self.assertFalse(pyrules.term.is_variable('X '))
        self.assertFalse(pyrules.term.is_variable(None))
        self.assertFalse(pyrules.term.is_variable('x'))
        self.assertFalse(pyrules.term.is_variable(42))
        self.assertFalse(pyrules.term.is_variable(('X', 'Y')))
        #is_valid_and_closed
        self.assertTrue(pyrules.term.is_valid_and_closed('a'))
        self.assertTrue(pyrules.term.is_valid_and_closed('bob'))
        self.assertTrue(pyrules.term.is_valid_and_closed(('parent', 'alice', 'bob')))
        self.assertFalse(pyrules.term.is_valid_and_closed('X'))
        self.assertFalse(pyrules.term.is_valid_and_closed(None))
        self.assertFalse(pyrules.term.is_valid_and_closed(42))
        self.assertFalse(pyrules.term.is_valid_and_closed('a b'))
        self.assertFalse(pyrules.term.is_valid_and_closed(('parent', 'X', 'bob')))
        #match
        self.assertIsInstance(self._term_match(('cons', 'X', 42), 'a'), pyrules.term.InvalidTerm)
        self.assertIsInstance(self._term_match(('cons', 'X', 'a'), ('cons', 42, 'a')), pyrules.term.InvalidTerm)
        self.assertIsInstance(self._term_match(('cons', 'X', 'a'), ('cons', 'X', 'a')), pyrules.term.OpenTerm)
        self.assertIsInstance(self._term_match('a', 'b'), pyrules.term.Mismatch)
        self.assertIsInstance(self._term_match('a', ('a', 'b')), pyrules.term.Mismatch)
        self.assertIsInstance(self._term_match(('a', 'X'), ('b', 'c')), pyrules.term.Mismatch)
        self.assertIsInstance(self._term_match(('a', 'X'), ('a', 'b', 'c')), pyrules.term.Mismatch)
        self.assertIsInstance(self._term_match(('a', 'X'), (('a', 'b'), 'c')), pyrules.term.Mismatch)
        self.assertIsInstance(self._term_match(('X', 'X'), ('a', 'b')), pyrules.term.Mismatch)
        self.assertEquals([None, None, None], self._term_match('a', 'a'))
        self.assertEquals([None, None, None], self._term_match(('a', 'b'), ('a', 'b')))
        self.assertEquals([None, None, None], self._term_match((('a', 'b'), 'c'), (('a', 'b'), 'c')))
        self.assertEquals(['a', None, None], self._term_match('X', 'a'))
        self.assertEquals(['a', None, None], self._term_match(('a', 'X'), ('a', 'a')))
        self.assertEquals(['a', None, None], self._term_match(('X', 'X'), ('a', 'a')))
        self.assertEquals(['a', 'b', None], self._term_match(('X', 'Y'), ('a', 'b')))
        self.assertEquals(['a', 'a', None], self._term_match(('X', 'Y'), ('a', 'a')))
        self.assertEquals(['a', 'b', None], self._term_match(('cons', 'X', ('cons', 'Y', 'nil')), 
                                                             ('cons', 'a', ('cons', 'b', 'nil'))))
        self.assertEquals(['a', 'b', 'c'], self._term_match(('cons', 'X', ('ctor', 'Y', 'X', ('Z', 'Z'))), 
                                                            ('cons', 'a', ('ctor', 'b', 'a', ('c', 'c')))))
        
    def _term_match(self, pattern_term, closed_term, lookup_variables = ['X', 'Y', 'Z']):
        try:
            binding = pyrules.term.match_and_bind(pattern_term, closed_term)
            return [binding.get(var, None) for var in lookup_variables]
        except Exception as e:
            return e
        
    def test_binding(self):
        b = Binding()
        self.assertEquals([], b.keys())
        b.bind('X', 'x')
        self.assertEquals([('X', 'x')], b.items())
        b.bind('Y', 'y')
        self.assertEquals([('X', 'x'), ('Y', 'y')], sorted(b.items()))
        b.bind('X', 'x')
        self.assertEquals([('X', 'x'), ('Y', 'y')], sorted(b.items()))
        self._fail_bind(b, 'Y', 'z')
        self._fail_bind(b, 'z', 'z')
        self._fail_bind(b, 'Z', 'W')
        self._fail_bind(b, 'Z orro', 'z')
        self._fail_bind(b, 'Z', 'z orro')

    def _fail_bind(self, binding, variable, term):
        try:
            binding.bind(variable, term)
            self.fail('Should not allow binding [{}]={}, but succeeded with result {}'.format(variable, term, binding))
        except Exception:
            pass
        
if __name__ == "__main__":
    unittest.main()