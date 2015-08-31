from itertools import imap, ifilter, product
from collections import deque
from uuid import uuid4
import urllib2
import urllib
import csv

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
        self._name = name

    def is_var(self):
        return False

    def __eq__(self, other):
        return isinstance(other, _Atom) and self._name == other._name

    def __ne__(self, other):
        if not isinstance(other, _Atom):
            return True
        return self._name != other._name

    def __hash__(self):
        return hash(self._name)

    def __str__(self):
        return 'atom.{}'.format(self._name)

    def __repr__(self):
        return '<atom.{}>'.format(self._name)

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

def wikipedia(func):
    #TODO: The method must be binary
    def resulting_method(self, x, y):
        return matches(_wikipedia_tuples(func.func_name), x, y)
    return resulting_method

_PARAMETERS = {'default-graph-uri' : 'http://dbpedia.org',
               'format' : 'text/csv',
               'timeout' : '30000'}
_Q1 = '''select * where {?x <http://dbpedia.org/property/'''
_Q2 = '''> ?y . FILTER (isURI(?y)) } LIMIT 200'''

def _wikipedia_tuples(name):
    #TODO Iterate over batches of 200, don't stop with the first
    pars = dict(_PARAMETERS)
    pars['query'] = _Q1 + name + _Q2
    url = 'http://dbpedia.org/sparql?' + urllib.urlencode(pars)
    csv_input = urllib2.urlopen(url, timeout=29)
    for row in csv.DictReader(csv_input):
        try:
            yield (_to_atom(row['x']), _to_atom(row['y']))
        except _NotDBpediaResource:
            pass

class _NotDBpediaResource(Exception):
    pass

_DBPRES = 'http://dbpedia.org/resource/'

def _to_atom(dbpedia_resource_url):
    parts = dbpedia_resource_url.split(_DBPRES)
    if len(parts) < 2:
        raise _NotDBpediaResource()
    return _Atom(parts[1])

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


