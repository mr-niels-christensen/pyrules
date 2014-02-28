import unittest
import pyrules.rulebook
import itertools
'''Example: Cellular automaton

   In this example, we're writing logic rules to compute successive generations
   of a cellular automaton. The automaton in question is "Rule 30" from Wolfram's "New Kind Of Science".
   
   NOTE: This is not an efficient implementation nor is it a handy representation for
   investigating cellular automata. The idea behind this implementation was to highlight
   challenges in writing simulation-like models for pyrules.
   
   In particular, 
'''
class Test(unittest.TestCase):
    def setUp(self):
        r = pyrules.rulebook.Rulebook()
        #First, the basic definition of "Rule 30"
        for (x, y, z) in [('0', '0', '0'),
                          ('1', '0', '1'),
                          ('1', '1', '0'),
                          ('1', '1', '1')]:
            r.rule('next', (x, y, z), '0')
        for (x, y, z) in [('0', '0', '1'),
                          ('0', '1', '0'),
                          ('0', '1', '1'),
                          ('1', '0', '0')]:
            r.rule('next', (x, y, z), '1')
        #Now define an initial configuration
        r.rule('generation', ('0', ('1', ('0',))))
        (
         r.rule('generation', 'GNEW')
         .premise('mapnext', '0', ('0', 'G'), 'GNEW') 
         .premise('generation', 'G')
        )
        #Finally, define how to map "Rule 30" on to a configuration
        (
         r.rule('mapnext', 'L', ('M', ('R', 'Rest')), ('B', 'More'))
         .premise('next', ('L', 'M', 'R'), 'B')
         .premise('mapnext', 'M', ('R', 'Rest'), 'More')
        )
        (
         r.rule('mapnext', 'L', ('M', ('R',)), ('BM', ('BR', ('BNEW',))))
         .premise('next', ('L', 'M', 'R'), 'BM')
         .premise('next', ('M', 'R', '0'), 'BR')
         .premise('next', ('R', '0', '0'), 'BNEW')
        )
        self.rulebook = r
    
    def test_first_10k(self):
        for term in itertools.islice(self.rulebook.generate_terms(trace = None), 10000):
            if term == ('generation', ('0', ('1', ('1', ('0', ('1', ('1', ('1', ('1', ('0',)))))))))):
                return
        self.fail('Did not manage to compute 3 generations in 10K steps as expected.')
            
if __name__ == "__main__":
    unittest.main()