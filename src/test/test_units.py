import unittest
from pyrules.binding import Binding
import pyrules.term 
import pyrules.rulebook
import itertools

class Test(unittest.TestCase):
    def test_rulebook_invalid_terms(self):
        self._assert_invalid_as_premise_or_conclusion('cons', 42, 'a')
        self._assert_invalid_as_premise_or_conclusion(None)
        self._assert_invalid_as_premise_or_conclusion('cons', (42, 'a'), 'a')
        self._assert_invalid_as_premise_or_conclusion('X', ['X'])
        
    def _assert_invalid_as_premise_or_conclusion(self, *invalid_term):    
        try:
            pyrules.rulebook.Rulebook().rule(*invalid_term)
            self.fail('Should have raised InvalidTerm')
        except pyrules.term.InvalidTerm:
            pass
        try:
            (
             pyrules.rulebook.Rulebook().rule('a')
             .premise(*invalid_term)
            )
            self.fail('Should have raised InvalidTerm')
        except pyrules.term.InvalidTerm:
            pass

    #Now for some overall Rulebook testing. Rulebook will be tested in more depth in separate integration tests.
    def test_rulebook_empty(self):
        r = pyrules.rulebook.Rulebook()
        self.assertEquals(0, len(list(r.generate_terms())))

    def test_rulebook_a(self):
        r = pyrules.rulebook.Rulebook()
        r.rule('a')
        self.assertSetEqual({'a'}, set(term for term in itertools.islice(r.generate_terms(), 100) if term is not None))

    def test_rulebook_ab(self):
        r = pyrules.rulebook.Rulebook()
        r.rule('a')
        (
         r.rule('b', 'X')
         .premise('X')
        )
        bs_and_a = set(term for term in itertools.islice(r.generate_terms(), 100) if term is not None)
        self.assertIn('a', bs_and_a)
        self.assertIn(('b', 'a'), bs_and_a)
        self.assertIn(('b', ('b', 'a')), bs_and_a)
        for term in bs_and_a:
            if term != 'a':
                self.assertEquals('b', term[0])
                self.assertIn(term[1], bs_and_a)
        
    def test_rulebook_no_terms(self):
        r = pyrules.rulebook.Rulebook()
        (
         r.rule('a', 'X')
         .premise('X')
        )
        (
         r.rule('b', 'X')
         .premise('X')
        )
        self.assertEquals(0, len(list(r.generate_terms())))

    def test_term(self):
        #is_variable
        self.assertTrue(pyrules.term.is_variable('X'))
        self.assertTrue(pyrules.term.is_variable('Distance'))
        self.assertFalse(pyrules.term.is_variable(''))
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
        self.assertFalse(pyrules.term.is_valid_and_closed(''))
        self.assertFalse(pyrules.term.is_valid_and_closed('X'))
        self.assertFalse(pyrules.term.is_valid_and_closed(None))
        self.assertFalse(pyrules.term.is_valid_and_closed(42))
        self.assertFalse(pyrules.term.is_valid_and_closed('a b'))
        self.assertFalse(pyrules.term.is_valid_and_closed(('parent', 'X', 'bob')))
        #check_valid
        self.assertTrue(Test._is_valid('a'))
        self.assertTrue(Test._is_valid('bob'))
        self.assertTrue(Test._is_valid(('parent', 'alice', 'bob')))
        self.assertFalse(Test._is_valid(''))
        self.assertTrue(Test._is_valid('X'))
        self.assertFalse(Test._is_valid(None))
        self.assertFalse(Test._is_valid(42))
        self.assertFalse(Test._is_valid('a b'))
        self.assertTrue(Test._is_valid(('parent', 'X', 'bob')))
        #match
        self.assertIsInstance(Test._term_match(('cons', 'X', 42), 'a'), pyrules.term.InvalidTerm)
        self.assertIsInstance(Test._term_match(('cons', 'X', 'a'), ('cons', 42, 'a')), pyrules.term.InvalidTerm)
        self.assertIsInstance(Test._term_match(('cons', 'X', 'a'), ('cons', 'X', 'a')), pyrules.term.OpenTerm)
        self.assertIsInstance(Test._term_match('a', 'b'), pyrules.term.Mismatch)
        self.assertIsInstance(Test._term_match('a', ('a', 'b')), pyrules.term.Mismatch)
        self.assertIsInstance(Test._term_match(('a', 'X'), ('b', 'c')), pyrules.term.Mismatch)
        self.assertIsInstance(Test._term_match(('a', 'X'), ('a', 'b', 'c')), pyrules.term.Mismatch)
        self.assertIsInstance(Test._term_match(('a', 'X'), (('a', 'b'), 'c')), pyrules.term.Mismatch)
        self.assertIsInstance(Test._term_match(('X', 'X'), ('a', 'b')), pyrules.term.Mismatch)
        self.assertEquals([None, None, None], Test._term_match('a', 'a'))
        self.assertEquals([None, None, None], Test._term_match(('a', 'b'), ('a', 'b')))
        self.assertEquals([None, None, None], Test._term_match((('a', 'b'), 'c'), (('a', 'b'), 'c')))
        self.assertEquals(['a', None, None], Test._term_match('X', 'a'))
        self.assertEquals(['a', None, None], Test._term_match(('a', 'X'), ('a', 'a')))
        self.assertEquals(['a', None, None], Test._term_match(('X', 'X'), ('a', 'a')))
        self.assertEquals(['a', 'b', None], Test._term_match(('X', 'Y'), ('a', 'b')))
        self.assertEquals(['a', 'a', None], Test._term_match(('X', 'Y'), ('a', 'a')))
        self.assertEquals(['a', 'b', None], Test._term_match(('cons', 'X', ('cons', 'Y', 'nil')), 
                                                             ('cons', 'a', ('cons', 'b', 'nil'))))
        self.assertEquals(['a', 'b', 'c'], Test._term_match(('cons', 'X', ('ctor', 'Y', 'X', ('Z', 'Z'))), 
                                                            ('cons', 'a', ('ctor', 'b', 'a', ('c', 'c')))))
        #substitute
        b_xyz = Binding()
        for (v, t) in [('X', 'a'), ('Y', 'b'), ('Z', ('c', 'c', 'c'))]:
            b_xyz.bind(v, t)
        self.assertEquals('a', pyrules.term.substitute('a', b_xyz))
        self.assertEquals('a', pyrules.term.substitute('X', b_xyz))
        self.assertEquals('b', pyrules.term.substitute('Y', b_xyz))
        self.assertEquals(('c', 'c', 'c'), pyrules.term.substitute('Z', b_xyz))
        self.assertEquals(('cons', ('c', 'c', 'c'), ('c', 'c', 'c')), pyrules.term.substitute(('cons', 'Z', 'Z'), b_xyz))
        self.assertEquals(('cons', ('cons', 'b', 'W'), ('c', 'c', 'c')), 
                          pyrules.term.substitute(('cons', ('cons', 'Y', 'W'), 'Z'), b_xyz))
        self.assertEquals(('cons', ('cons', 'Y', 'W'), 'Z'), pyrules.term.substitute(('cons', ('cons', 'Y', 'W'), 'Z'), Binding()))
        self.assertIsInstance(Test._substitute(None, Binding()), pyrules.term.InvalidTerm)
        self.assertIsInstance(Test._substitute('X', None), Exception)

    @staticmethod
    def _is_valid(term):
        try:
            pyrules.term.check_valid(term)
            return True
        except pyrules.term.InvalidTerm:
            return False
    
    @staticmethod
    def _substitute(term, binding):
        try:
            return pyrules.term.substitute(term, binding)
        except Exception as e:
            return e

    @staticmethod
    def _term_match(pattern_term, closed_term, lookup_variables = ['X', 'Y', 'Z']):
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
