import pyrules.term
import Queue
import itertools

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
        pyrules.term.check_valid(conclusion_term)
        index = len(self._rules)
        self._rules.append((conclusion_term, set()))
        return _Rule(self, index)
    
    def _add_premise(self, index, premise):
        '''Adds one premise to the rule with the given index.
           @param index: Index into the internal list of rules.
           @param premise: The added premise of the rule. Must be a tuple.
           If the tuple contains exactly one term, the new premise
           will be that term, otherwise the new premise will be the tuple itself.
        '''
        premise_term = premise if len(premise) != 1 else premise[0]
        pyrules.term.check_valid(premise_term)
        self._rules[index][1].add(premise_term)
        
    def generate_terms(self):
        '''Generator for all terms that can be concluded from the rules in this Rulebook.
           The generator operates as if the Rulebook is "copied", i.e. future updates of the Rulebook
           will not affect the generator's returned result.
           Note: The generated sequence may contain (many) occurrences of None.
           The generated sequence is will be infinite if and only if the rules generate infinitely many terms.
        '''
        session = _Session()
        for (conclusion_term, premise_term_set) in self._rules:
            session.add_rule(conclusion_term, premise_term_set)
        return session.stream()
    
class _Rule(object):
    '''Helper object for implementing chaining of .premise() method.
    '''
    def __init__(self, rulebook, index):
        self.index = index
        self.rulebook = rulebook
    
    def premise(self, *premise):
        '''Implements a chainable interface to Rulebook._add_premise()
        '''
        self.rulebook._add_premise(self.index, premise)
        return self
    
class _Session(object):
    '''A _Session is a process that generates all terms for a Rulebook.
    
       The overall algorithm is centered around a queue. Each queue element
       corresponds to a match between a premise from the Rulebook and an already
       generated term. Each queue element has the form (binding, rule_index, premise_index) where
        - binding is the binding resulting from the match,
        - rule_index is the index of the rule of the matching premise
        - premise_index is the index of the premise within that rule.
       Whenever a term has been generated, it is matched to every premise in the Rulebook,
       and successful matches are put on the queue before yielding the term to the caller.
       
       When the _Session needs to generate a new term, it takes one match, (b, r_i, p_i) off the queue.
       It then proceeds to generate all conclusions of rule r_i where p_i is bound by b
       and the other premises of r_i are bound by bindings previously taken off the queue.
       (Early in the process some premises may have no bindings so that no conclusions can be generated).
       
       The process is boostrapped using the facts (0-premise rules) from the Rulebook.
       
       To avoid unbounded waiting, None is generated when bound premises are incompatible,
       e.g. for the rule X :- ('a', 'X'), ('b', 'X') when the first premise is bound by
       {'X' : 'c'} and the second premise is bound to {'X' : 'd'}. 
    '''
    def __init__(self):
        '''Initiates a _Session with no rules.
           Call add_rule() to add the rules, then call stream() to generate terms.
        '''
        self._conclusions = [] #Conclusions of the non-fact rules given to add_rule()
        self._active_bindings = [] #A list of lists of bindings taken off the queue, organized as _active_bindings[rule_index][premise_index] 
        self._binding_q = _MatchQueue() #The queue of matches. This will perform the matching and remove terms already seen.
        self._facts = [] #Facts given to add_rule()
        
    def add_rule(self, conclusion_term, premise_terms):
        '''Adds the given rule to internal data structures.
        '''
        if len(premise_terms) == 0: #A fact
            self._facts.append(conclusion_term)
        else:
            rule_index = len(self._conclusions)
            self._conclusions.append(conclusion_term)
            self._active_bindings.append([[] for _ in premise_terms])
            for (premise_index, premise_term) in enumerate(premise_terms):
                self._binding_q.add_premise(premise_term, rule_index, premise_index)
    
    def stream(self):
        '''Generator method yielding all terms generated by the given rules,
           with the possibility of (many) None values in between.
           The reason for allowing None values is that a page of values should
           be generated in reasonable time.
        '''
        #First generate all facts and add them to the queue.
        for fact in self._facts:
            self._binding_q.add_term(fact)
            yield fact
        while True:#Loop until the queue is empty
            try:
                (b, rule_index, premise_index) = self._binding_q.get(block = False) #Get one match
                binding_list_per_premise = [(binding_list if index != premise_index else [b]) 
                                            for (index, binding_list) 
                                            in enumerate(self._active_bindings[rule_index]) 
                                            ] #Active bindings = previously taken off the queue
                #Now yield all terms generated by combinations of these bindings
                for binding_per_premise in itertools.product(*binding_list_per_premise):#Pick one binding per premise
                    substituted_conclusion = term_or_None(self._conclusions[rule_index], binding_per_premise)
                    if substituted_conclusion is not None:
                        self._binding_q.add_term(substituted_conclusion)
                    yield substituted_conclusion
                #Add the most recently gotten match to the active bindings
                self._active_bindings[rule_index][premise_index].append(b)
            except Queue.Empty:
                return
            
def term_or_None(conclusion_term, binding_iter):
    '''Substitutes variables in conclusion_term with their bindings in binding_iter.
       If two bindings in binding_iter are incompatible (binds the same variable to different values),
       this method returns None.
       @param conclusion_term: A term.
       @param binding_iter: An iterable of bindings.
       @return: The result of substituting variables in conclusion_term with their bindings in binding_iter,
       or None.
    '''
    try:
        b = pyrules.binding.Binding()
        for binding in binding_iter:
            b.add_all(binding)
        return pyrules.term.substitute(conclusion_term, b)
    except pyrules.binding.InvalidBinding:
        return None
    
class _MatchQueue(Queue.Queue):
    '''A queue for matches on the form (binding, rule_index, premise_index).
       The _MatchQueue is responsible for forming match tuples for a given term.
       It also removes terms already seen.
       
       So to use a configuration _MatchQueue, simply call add_term() and get().
    '''
    def __init__(self):
        '''Constructs a _MatchQueue with no premises to match.
           Call add_premise() to make add_term useful.
        '''
        Queue.Queue.__init__(self)
        self._premises = []
        self._seen_terms = set()
        
    def add_premise(self, premise_term, rule_index, premise_index):
        '''Adds the given premise to this _MatchQueue.
           When a term matches premise_term, the resulting binding
           will be enqueued along with rule_index and premise_index.
        '''
        self._premises.append((premise_term, rule_index, premise_index))
        
    def add_term(self, closed_term):
        '''Matches closed_term to all premises given to add_premise().
           In case of a successful match, the resulting binding
           will be enqueued along with rule_index and premise_index.
        '''
        if not pyrules.term.is_valid_and_closed(closed_term):
            raise pyrules.term.OpenTerm
        if closed_term in self._seen_terms:
            return
        for (premise_term, rule_index, premise_index) in self._premises:
            try:
                b = pyrules.term.match_and_bind(premise_term, closed_term)
                self.put((b, rule_index, premise_index))
            except pyrules.term.Mismatch:
                pass
