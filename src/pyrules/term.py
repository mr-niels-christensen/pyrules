# -*- coding: utf-8 -*- 
import collections

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
    pass
