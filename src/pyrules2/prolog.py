from itertools import imap, ifilter, product
from collections import deque
from prolog_like_terms import _Namespace, _Var, _Atom

class RuleBook(object):
    pass

var = _Namespace(_Var)
atom = _Namespace(_Atom)

def matches(tuple_iterator, *args):
    #TODO consider better syntactical sugar, e.g. find(x,y).in([...])
    #or something corresponding to reduce(|,match(x,y,foo) for foo in [...])
    #or @rule(style=tuples) def p(x,y): return [...]
    var_indexes = dict()
    #TODO handle when same var appears multipe times
    for index, arg in enumerate(args):
        if arg.is_var():
            var_indexes[arg] = index
        else:
            tuple_iterator = ifilter(lambda t: t[index] == arg, tuple_iterator)
    map = lambda t : {v : t[var_indexes[v]] for v in var_indexes}
    return _Wrap(map(t) for t in tuple_iterator)

def rule(func):
    def resulting_method(self, *args):
        assert all(isinstance(arg, _Var) or isinstance(arg, _Atom) for arg in args)
        return func(self, *args).set_args(*args)
    return resulting_method

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


