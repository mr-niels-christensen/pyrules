# -*- coding: utf-8 -*- 
import unittest
import pyrules.rulebook
import itertools
import pyrules.term

ATOMIC_PROPOSITIONS = ['p', 'q']

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
        
    def _add_equivalence(self, rel):
        ( #Reflexive
        self.r.rule(rel, 'X', 'X')
        .premise('expr', 'X')
        )
        ( #Symmetric
        self.r.rule(rel, 'X', 'Y')
        .premise(rel, 'Y', 'X')
        )
        ( #Transitive
        self.r.rule(rel, 'X', 'Z')
        .premise(rel, 'X', 'Y')
        .premise(rel, 'Y', 'Z')
        )

    def _add_equation(self, lhs, rhs):
        variables = set()
        pyrules.term._atoms_and_variables(lhs, set(), variables)
        pyrules.term._atoms_and_variables(rhs, set(), variables)
        rule = self.r.rule('=', lhs, rhs)
        for v in variables:
            rule.premise('expr', v)

    def setUp(self):
        self.r = pyrules.rulebook.Rulebook()
        self._add_equivalence('=')
        for p in ATOMIC_PROPOSITIONS:
            self.r.rule('expr', p)
        self._add_binop('∧')
        self._add_binop('∨')
        self._add_unop('¬')
        self._add_equation(('∧', 'A', 'B'), ('∧', 'B', 'A')) #Commutativity of AND
        self._add_equation(('∨', 'A', 'B'), ('∨', 'B', 'A')) #Commutativity of OR
        self._add_equation(('∧', 'A', ('∨', 'B', 'C')), #Distributivity of AND
                           ('∨', ('∧', 'A', 'B'), ('∧', 'A', 'C')))
        self._add_equation(('∨', 'A', ('∧', 'B', 'C')), #Distributivity of OR
                           ('∧', ('∨', 'A', 'B'), ('∨', 'A', 'C')))
        self._add_equation('A', #A = A ∧ (B ∨ ¬B)
                           ('∧', 'A', ('∨', 'B', ('¬', 'B'))))
        self._add_equation('A', #A = A ∨ (B ∧ ¬B)
                           ('∨', 'A', ('∧', 'B', ('¬', 'B'))))

    def test_no_repetitions(self):
        seen = set()
        for term in itertools.islice(self.r.generate_terms(), 1000):
            if term in seen:
                self.fail('Saw {} twice after {} terms were generated'.format(term, len(seen)))
            if term is not None and Test.pp(term).startswith('q ='.encode('utf-8')):
                print '{}: {}'.format(len(seen), Test.pp(term))
            seen.add(term)

    def test_fact_found(self):
        seen = set()
        for term in itertools.islice(self.r.generate_terms(), 1000):
            if term in seen:
                self.fail('Saw {} twice after {} terms were generated'.format(term, len(seen)))
            if term is not None and Test.pp(term).startswith('q ='.encode('utf-8')):
                print '{}: {}'.format(len(seen), Test.pp(term))
            seen.add(term)

    @staticmethod
    def pp(fact):
        if fact is None:
            return None
        if isinstance(fact, tuple) and len(fact) == 3 and fact[0] == '=':
            return '{} = {}'.format(Test.pp(fact[1]), Test.pp(fact[2]))
        if isinstance(fact, tuple) and len(fact) == 3:
            return '({} {} {})'.format(Test.pp(fact[1]), Test.pp(fact[0]), Test.pp(fact[2]))
        if isinstance(fact, tuple) and len(fact) == 2:
            return '{}{}'.format(Test.pp(fact[0]), Test.pp(fact[1]))
        return fact.encode('utf-8')


if __name__ == "__main__":
    unittest.main()