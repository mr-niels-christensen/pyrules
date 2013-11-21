import term

class Binding(dict):
    '''
    A Binding is a dict for mapping each variable of a Term
    to a closed term without variables in them.
    '''
    
    def bind(self, variable, closed_term):
        '''Adds a mapping if the given variable was not mapped before or was
           mapped to the same closed term. Raises an Exception if the given
           variable was already mapped to a different term.
           @param variable: The name of the variable to bind, e.g. 'X'
           @param closed_term: A term without variables, represented as
           a unicode, str or tuple.
        '''
        if not term.is_variable(variable):
            raise InvalidBinding('Cannot bind non-variable {}'.format(variable))
        if not term.is_valid_and_closed(closed_term):
            raise InvalidBinding('{} is not a valid, closed term'.format(closed_term))
        if variable in self and closed_term != self[variable]:
            raise InvalidBinding('Cannot bind {} to {}; already bound to {}'.format(variable, closed_term, self[variable]))
        self[variable] = closed_term
    
class InvalidBinding(Exception):
    pass
