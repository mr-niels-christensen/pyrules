# -*- coding: utf-8 -*- 
import unittest
import pyrules.rulebook
import itertools
import pyrules.term

ATOMIC_PROPOSITIONS = ['p', 'q']

def _implies(lhs, rhs):
    return ('∨', ('¬', lhs), rhs)
    
class Test(unittest.TestCase):

    def _add_binop(self, op):
        (
         self.r.rule('expr', (op, 'X', 'Y'))
         .premise('expr', 'X')
         .premise('expr', 'Y')
        )
        
    def _add_unop(self, op):
        (
         self.r.rule('expr', (op, 'X'))
         .premise('expr', 'X')
        )
    
    def setUp(self):
        self.r = pyrules.rulebook.Rulebook()
        for p in ATOMIC_PROPOSITIONS:
            self.r.rule('expr', p)
        self._add_binop('∨')
        self._add_unop('¬')
        #Russell-Bernays axiom system:
        (
         self.r.rule('true', 'B')
         .premise('true', 'A')
         .premise('true', _implies('A', 'B'))
        )
        (
         self.r.rule('true', 
                     _implies(_implies('B', 'C'),
                              _implies(('∨', 'A', 'B'),
                                       ('∨', 'A', 'C'))))
         .premise('expr', 'A')
         .premise('expr', 'B')
         .premise('expr', 'C')
        )
        (
         self.r.rule('true', 
                     _implies(('∨', 'A', 'B'),
                              ('∨', 'B', 'A')))
         .premise('expr', 'A')
         .premise('expr', 'B')
        )
        (
         self.r.rule('true', 
                     _implies('A',
                              ('∨', 'B', 'A')))
         .premise('expr', 'A')
         .premise('expr', 'B')
        )
        (
         self.r.rule('true', 
                     _implies(('∨', 'A', 'A'),
                              'A'))
         .premise('expr', 'A')
        )
        
    def test_fact_found(self):
        terms_1000 = [term for term in itertools.islice(self.r.generate_terms(), 1000) if term is not None]
        true_facts_1000 = [term for (tag, term) in terms_1000 if tag == 'true']
        self.assertIn(('∨', ('¬', ('¬', 'p')), 
                            ('∨', ('¬', 'q'), ('¬', 'p'))), 
                      true_facts_1000)

    @staticmethod
    def pp(fact):
        if fact is None:
            return None
        if isinstance(fact, tuple) and len(fact) == 3:
            return '({} {} {})'.format(Test.pp(fact[1]), Test.pp(fact[0]), Test.pp(fact[2]))
        if isinstance(fact, tuple) and len(fact) == 2:
            return '{}{}'.format(Test.pp(fact[0]), Test.pp(fact[1]))
        return fact.encode('utf-8')


if __name__ == "__main__":
    unittest.main()