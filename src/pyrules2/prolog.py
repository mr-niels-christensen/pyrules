from itertools import imap, ifilter, product
from collections import deque
from uuid import uuid4

class RuleBook(object):
    pass

class _Namespace(object):
    def __init__(self, ctor):
        self._ctor = ctor

    def __getattr__(self, name):
        return self._ctor(name)

class _Var(object):
    def __init__(self, name):
        self._name = '{}_{}'.format(name, str(uuid4()).replace('-','_'))
                
    def is_var(self):
        return True

    def __eq__(self, other):
        return isinstance(other, _Var) and self._name == other._name

    def __hash__(self):
        return hash(self._name)

    def __str__(self):
        return '?{}'.format(self._name)

    def __repr__(self):
        return '<?{}>'.format(self._name)

class _Atom(object):
    def __init__(self, name):
        #TODO Associate with Rulebook?
        self._name = name

    def is_var(self):
        return False

    def __eq__(self, other):
        return isinstance(other, _Atom) and self._name == other._name

    def __ne__(self, other):
        if not isinstance(other, _Atom):
            return True
        return self._name != other._name

    def __str__(self):
        return 'atom.{}'.format(self._name)

    def __repr__(self):
        return '<atom.{}>'.format(self._name)

var = _Namespace(_Var)
atom = _Namespace(_Atom)

def pairs(pairs_iterator):
    #TODO Make into a decorator object
    cached = set(pairs_iterator)
    #TODO Check/use func's arguments and allow kwargs
    def actual_decorator(_func):
        def resulting_method(self, *args):
            assert len(args) == 2
            assert isinstance(args[0], _Var) or isinstance(args[0], _Atom)
            assert isinstance(args[1], _Var) or isinstance(args[1], _Atom)
            #TODO: Allow call with no variables
            assert args[0].is_var() or args[1].is_var()
            #TODO: Wrap in a formatter, unpacking dicts
            return _wrap_pairs_iterator(cached, *args)
        return resulting_method
    return actual_decorator

def rule(func):
    def resulting_method(self, *args):
        assert all(isinstance(arg, _Var) or isinstance(arg, _Atom) for arg in args)
        return func(self, *args).set_args(*args)
    return resulting_method

def _wrap_pairs_iterator(pairs_iterator, arg0, arg1):
        if arg0.is_var() and arg1.is_var():
            wrapped = ({arg0:x, arg1:y} for (x, y) in pairs_iterator)
            return _Wrap(wrapped).set_args(arg0, arg1)
        if arg0.is_var():
            wrapped = ({arg0:x} for (x, y) in pairs_iterator if y == arg1)
            return _Wrap(wrapped).set_args(arg0, arg1)
        if arg1.is_var():
            wrapped = ({arg1:y} for (x, y) in pairs_iterator if x == arg0)
            return _Wrap(wrapped).set_args(arg0, arg1)

class _Wrap(object):
    def __init__(self, wrapped):
        self._wrapped = wrapped
        self._projection = lambda d : d

    def set_args(self, *args):
        self._projection = lambda d : tuple(d[arg] for arg in args if arg.is_var())
        return self

    def __iter__(self):
        return self

    def next(self):
        n = self._wrapped.next()
        return self._projection(n)

    def __and__(self, other):
        #TODO: propagate bindings!
        assert isinstance(other, _Wrap)
        prod = product(self._wrapped, other._wrapped)
        return _Wrap(imap(_union, ifilter(_compatible, prod)))

    def __or__(self, other):
        assert isinstance(other, _Wrap)
        return _Wrap(roundrobin(self._wrapped, other._wrapped))

def _union(ds):
    d0, d1 = ds
    d = d0.copy()
    d.update(d1)
    return d

def _compatible(ds):
    d0, d1 = ds
    for key in d0:
        if key in d1 and d0[key] != d1[key]:
            return False
    return True

def roundrobin(*iterables):
    '''Splices the given iterables, see
       http://bugs.python.org/issue1757395
    '''
    pending = deque(iter(i).next for i in reversed(iterables))
    rotate, pop, _StopIteration = pending.rotate, pending.pop, StopIteration
    while pending:
        try:
            while 1:
                yield pending[-1]()
                rotate()
        except _StopIteration:
            pop()


