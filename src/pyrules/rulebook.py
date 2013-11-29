class Rulebook(object):
    '''A Rulebook defines a recursive scheme for generating terms.
       The Rulebook contains a number of rules.
       Each rule has one term as its "conclusion", and zero or more
       terms as its "premises".
       
       Example: For every term generated by the Rulebook, the 1-premise rule
                    ('a', 'X') :- 'X'
                generates one new term. Say 'b' was generated by some other rule.
                Then ('a', 'b') will be generated by the above rule. So will ('a', ('a', 'b')), eventually.
       
       When each premise of a rule matches some already generated term, the rule can "fire",
       generating its conclusion term with its variables substituted by the bindings
       obtained from the matches.
       
       A number of concrete examples will appear in the test package.
    '''
    
    def __init__(self):
        self._rules = []
        
    def rule(self, *conclusion):
        '''Adds one rule to this Rulebook. To add premises to the rule,
           use a chain of "premise" method calls to the return value like this:
             rb.rule(conclusion).premise(premise0).premise(premise1).premise(2)
           The premise methods use the same notation discussed for param conclusion below.
           @param conclusion: The conclusion of the rule.
           If exactly one value is passed to this method, the new rule's conclusion
           will be that term.
           If more than one value is passed, the conclusion will be a tuple with the given
           values as elements.
           Example: rb.rule('a', 'X') adds a rule with the term ('a', 'X') as its conclusion.
           Example: rb.rule('X') adds a rule with the term 'X' as its conclusion (not the tuple ('X')).
           @return: An object with a method premise() for adding a premise to the new rule.
           This method will also return an object that implements premise() so calls can be chained.
           The notation for premise terms is the same as for the conclusion term. 
        '''
        conclusion_term = conclusion if len(conclusion) != 1 else conclusion[0]
        index = len(self._rules)
        self._rules.append((conclusion_term, []))
        return _Rule(self, index)
    
    def _add_premise(self, index, premise):
        '''Adds one premise to the rule with the given index.
           @param index: Index into the internal list of rules.
           @param premise: The added premise of the rule. Must be a tuple.
           If the tuple contains exactly one term, the new premise
           will be that term, otherwise the new premise will be the tuple itself.
        '''
        premise_term = premise if len(premise) != 1 else premise[0]
        self._rules[index][1].append(premise_term)
        
    def generate_terms(self):
        '''Generator for all terms that can be concluded from the rules in this Rulebook.
           The generator operates as if the Rulebook is "copied", i.e. future updates of the Rulebook
           will not affect the generator's returned result.
           Note: The generated sequence may contain (many) occurrences of None.
           This is not an indication that there are no more terms to generate.
           This implementation does not give an indication if there are no more terms to generate.
           The generated sequence is guaranteed to be infinite.
        '''
        raise Exception('Not implemented yet')
    
class _Rule(object):
    '''Helper object for implementing chaining of .premise() method.
    '''
    def __init__(self, rulebook, index):
        self.index = index
        self.rulebook = rulebook
    
    def premise(self, *premise):
        self.rulebook._add_premise(self.index, premise)
        return self
