# -*- coding: utf-8 -*- 
import unittest
import pyrules.rulebook
import itertools
'''This examples show how pyrules can be used to work with mathematical logic in Python.

   The setUp() method creates a RuleBook for propositional logic,
   based on the Russell-Bernays axiom system (which happens to be reasonably
   small and only uses the connectives for OR and NOT).
   
   The RuleBook will generated all theorems of that axiom system using the atomic propositions
   'p' and 'q'. 
'''
ATOMIC_PROPOSITIONS = ['p', 'q']

def _implies(lhs, rhs):
    '''All 5 axioms are implications, so they're easier to read with this abbreviation. 
    '''
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
        (#When A and A=>B are true, so is B
         self.r.rule('true', 'B')
         .premise('true', 'A')
         .premise('true', _implies('A', 'B'))
        )
        (#(B=>C) => ((A∨B) => (A∨C)) is true when A,B,C are expressions
         self.r.rule('true', 
                     _implies(_implies('B', 'C'),
                              _implies(('∨', 'A', 'B'),
                                       ('∨', 'A', 'C'))))
         .premise('expr', 'A')
         .premise('expr', 'B')
         .premise('expr', 'C')
        )
        (#(A=>B) => (B∨A) is true when A,B are expressions
         self.r.rule('true', 
                     _implies(('∨', 'A', 'B'),
                              ('∨', 'B', 'A')))
         .premise('expr', 'A')
         .premise('expr', 'B')
        )
        (#A => (B∨A) is true when A,B are expressions
         self.r.rule('true', 
                     _implies('A',
                              ('∨', 'B', 'A')))
         .premise('expr', 'A')
         .premise('expr', 'B')
        )
        (#(A∨A) => A is true when A is an expression
         self.r.rule('true', 
                     _implies(('∨', 'A', 'A'),
                              'A'))
         .premise('expr', 'A')
        )
        
    def test_fact_found(self):
        '''Verify that one particular truth is generated
        '''
        terms_1000 = [term for term in itertools.islice(self.r.generate_terms(), 1000) if term is not None]
        true_facts_1000 = [term for (tag, term) in terms_1000 if tag == 'true']
        self.assertIn(('∨', ('¬', ('¬', 'p')), 
                            ('∨', ('¬', 'q'), ('¬', 'p'))), 
                      true_facts_1000)

    def test_always_true(self):
        '''Verify that all (initial) generated 'true' terms
           evaluate to true no matter the values of the ATOMIC_PROPOSITIONS
        '''
        for term in itertools.islice(self.r.generate_terms(), 1000):
            if term is not None and term[0] == 'true':
                self._assert_true(term[1], p = True, q = True)
                self._assert_true(term[1], p = True, q = False)
                self._assert_true(term[1], p = False, q = True)
                self._assert_true(term[1], p = False, q = False)

    def _assert_true(self, expr, p, q):
        true_atomic_propositions = set()
        if p:
            true_atomic_propositions.add('p')
        if q:
            true_atomic_propositions.add('q')
        self.assertTrue(Test._evaluate(expr, true_atomic_propositions),
                        '{} is not true when p={} and q={}'.format(Test.pp(expr), p, q))

    @staticmethod
    def _evaluate(expr, true_atomic_propositions):
        if expr[0] == '¬':
            return not Test._evaluate(expr[1], true_atomic_propositions)
        if expr[0] == '∨':
            return Test._evaluate(expr[1], true_atomic_propositions) or Test._evaluate(expr[2], true_atomic_propositions)
        return expr in true_atomic_propositions
        
    @staticmethod
    def pp(fact):
        if fact is None:
            return None
        if isinstance(fact, tuple) and len(fact) == 3:
            return '({} {} {})'.format(Test.pp(fact[1]), Test.pp(fact[0]), Test.pp(fact[2]))
        if isinstance(fact, tuple) and len(fact) == 2:
            return '{}{}'.format(Test.pp(fact[0]), Test.pp(fact[1]))
        return fact


if __name__ == "__main__":
    unittest.main()