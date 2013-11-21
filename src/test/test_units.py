import unittest
from pyrules.binding import Binding
import pyrules.term 

class Test(unittest.TestCase):
    def test_term(self):
        self.assertTrue(pyrules.term.is_variable('X'))
        self.assertTrue(pyrules.term.is_variable('Distance'))
        self.assertFalse(pyrules.term.is_variable(' X'))
        self.assertFalse(pyrules.term.is_variable('X '))
        self.assertFalse(pyrules.term.is_variable(None))
        self.assertFalse(pyrules.term.is_variable('x'))
        self.assertFalse(pyrules.term.is_variable(42))
        self.assertFalse(pyrules.term.is_variable(('X', 'Y')))
        self.assertTrue(pyrules.term.is_valid_and_closed('a'))
        self.assertTrue(pyrules.term.is_valid_and_closed('bob'))
        self.assertTrue(pyrules.term.is_valid_and_closed(('parent', 'alice', 'bob')))
        self.assertFalse(pyrules.term.is_valid_and_closed('X'))
        self.assertFalse(pyrules.term.is_valid_and_closed(None))
        self.assertFalse(pyrules.term.is_valid_and_closed(42))
        self.assertFalse(pyrules.term.is_valid_and_closed('a b'))
        self.assertFalse(pyrules.term.is_valid_and_closed(('parent', 'X', 'bob')))
        
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