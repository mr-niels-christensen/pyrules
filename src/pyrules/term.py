# -*- coding: utf-8 -*- 
import collections
import binding

'''
Methods for validating and matching terms.
We allow three kinds of terms:
  - A variable, represented as a unicode or a str without whitespaces,
    and beginning with a capital letter. Examples: 'X', 'Distance'
  - An atom, represented as a unicode or a str without whitespaces,
    beginning with anything but a capital letter. Examples: 'bob', '¬'
  - An iterable of valid terms. Example: ('parent', 'alice', 'bob').
    The empty iterable is a valid term.
'''

def substitute(term, binding):
    '''Example result: b = Binding()
                       b.bind('X', 'a')
                       substitute(('cons', X', 'X'), b) == ('cons', 'a', 'a')  
       @param term: Any valid term. (If not valid, an InvalidTerm will be raised).
       @param binding: Any pyrules.binding.Binding
       @return: A copy of term with every occurrence of a variable bound in binding
                replace by the term it is bound to.
    '''
    raise Exception('Not implemented yet')

def match_and_bind(pattern_term, closed_term):
    '''Matches pattern_term to closed_term. If the terms match,
       creates a binding of all variables in pattern_term to the
       corresponding subterms in closed_term.
       Example: After b = match_and_bind(('X', 'b', 'Z'), ('a', 'b', 'c'))
                then  b['X'] == 'a' and b['Z'] == 'c'
       If the two terms did not match, a Mismatch will be raised.
       @param pattern_term: Any valid pattern
       @param closed_term: A valid, closed pattern.
       @return: A binding for the match.
    '''
    _atoms_and_variables(pattern_term, set(), set()) #Raises InvalidTerm if pattern_term is not valid
    check = set()
    _atoms_and_variables(closed_term, set(), check) #Raises InvalidTerm if closed_term is not valid
    if len(check) > 0:
        raise OpenTerm('Found variables {} in supposedly closed term {}'.format(check, closed_term))
    try:
        b = binding.Binding()
        _match_and_add_bindings(pattern_term, closed_term, b)
        return b
    except binding.InvalidBinding:
        raise Mismatch()

def _match_and_add_bindings(pattern_term, closed_term, binding):
    '''Matches pattern_term to closed_term. If the terms match,
       adds bindings of all variables in pattern_term to binding.
       If the two terms did not match, a Mismatch will be raised.
       In that case, some binding may already have been added to binding
       @param pattern_term: Any valid pattern. Must be checked before calling.
       @param closed_term: A valid, closed pattern. Must be checked before calling.
       @param binding: pyrules.binding.Binding to add relevant bindings to.
    '''
    
    if is_variable(pattern_term):
        binding.bind(pattern_term, closed_term)
    elif _is_valid_atom_or_variable(pattern_term): #i.e. an atom
        if pattern_term != closed_term:
            raise Mismatch()
    else: #pattern_term is iterable
        if isinstance(closed_term, collections.Iterable) and len(closed_term) == len(pattern_term):
            for (pt, ct) in zip(pattern_term, closed_term):
                _match_and_add_bindings(pt, ct, binding)
        else:
            raise Mismatch()
        
def is_valid_and_closed(term):
    '''@param term: Any value.
       @return: True, if term is a valid term and does not contain any variable.
                Returns False otherwise.
    '''
    variables = set()
    try:
        _atoms_and_variables(term, set(), variables)
        return len(variables) == 0
    except InvalidTerm:
        return False 

def is_variable(term):
    '''@param term: Any value.
       @return: True if term is a valid term and is a variable.
                Returns False otherwise.
    '''
    return _is_valid_atom_or_variable(term) and term[0].isupper()

def _is_valid_atom_or_variable(term):
    '''@param term: Any value.
       @return: True if term is a valid term and is an atom or a variable.
                Returns False otherwise.
    '''
    return isinstance(term, basestring) and len(term) > 0 and len(term.split(None, 1)) == 1 and term.strip() == term

def _atoms_and_variables(term, atoms, variables):
    '''Raises InvalidTerm if term is not a valid term.
       Otherwise, adds all atoms in term to atoms and all variables in
       term to variables.
       @param term: Any value
       @param atoms: A set to collect atoms in
       @param variables: A set to collect variables in
    '''
    if is_variable(term):
        variables.add(term)
    elif _is_valid_atom_or_variable(term):
        atoms.add(term)
    elif isinstance(term, basestring):
        raise InvalidTerm('Invalid string term "{}"'.format(term))
    elif isinstance(term, collections.Iterable):
        for subterm in term:
            _atoms_and_variables(subterm, atoms, variables)
    else:
        raise InvalidTerm('Invalid Python type {} of {}'.format(type(term), term))
        
class InvalidTerm(Exception):
    '''A given term was not valid, as defined by the criteria at the top of this file.
    '''
    pass

class OpenTerm(Exception):
    '''An open term (one with variables) was given in a context where only
       a closed term is allowed.
    '''
    pass

class Mismatch(Exception):
    '''Attempted to match two terms that did not match, e.g. ('a', 'X') to ('b', 'c').
    '''
    pass
