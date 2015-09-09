from itertools import imap, ifilter, product, islice
from collections import deque
from prolog_like_terms import is_term
from functools import wraps


class RuleBook(object):
    pass


class _ParseTree(object):
    MATCHES, AND, OR, LIMIT = range(4)
    NODE_TYPES = set([MATCHES, AND, OR, LIMIT])

    def __init__(self, node_type, *sub_trees, **parameters):
        assert node_type in _ParseTree.NODE_TYPES
        self._node_type = node_type
        self._sub_trees = sub_trees
        self._parameters = parameters

    def __and__(self, other):
        assert isinstance(other, _ParseTree)
        return _ParseTree(_ParseTree.AND, self, other)

    def __or__(self, other):
        assert isinstance(other, _ParseTree)
        return _ParseTree(_ParseTree.OR, self, other)

    def to_dict_iterator(self):
        sub_iterators = [s.to_dict_iterator() for s in self._sub_trees]
        if self._node_type == _ParseTree.MATCHES:
            return _dict_iterator_for_matches(self._parameters['tuple_iterator'],
                                              self._parameters['args'])
        elif self._node_type == _ParseTree.AND:
            return imap(_union, ifilter(_compatible, product(*sub_iterators)))
        elif self._node_type == _ParseTree.OR:
            return _roundrobin(*sub_iterators)
        elif self._node_type == _ParseTree.LIMIT:
            return islice(sub_iterators[0], self._parameters['max_results'])
        else:
            raise Exception('Invalid node type: {}'.format(self._node_type))


def limit(max_results):
    def _limit(method):
        def _resulting_method(self, *args, **kwargs):
            return _ParseTree(
                _ParseTree.LIMIT,
                method(self, *args, **kwargs),
                max_results=max_results)
        return wraps(method)(_resulting_method)
    return _limit


def matches(tuple_iterator, *args):
    # TODO consider better syntactical sugar, e.g. find(x,y).in([...])
    # or something corresponding to reduce(|,match(x,y,foo) for foo in [...])
    # or @rule(style=tuples) def p(x,y): return [...]
    return _ParseTree(
        _ParseTree.MATCHES,
        tuple_iterator=tuple_iterator,
        args=args)


def _dict_iterator_for_matches(tuple_iterator, args):
    var_indexes = dict()
    # TODO handle when same var appears multiple times
    for index, arg in enumerate(args):
        if arg.is_var():
            var_indexes[arg] = index
        else:
            tuple_iterator = ifilter(lambda t: t[index] == arg, tuple_iterator)
    map = lambda t: {v: t[var_indexes[v]] for v in var_indexes}
    return (map(t) for t in tuple_iterator)


def rule(func):
    def resulting_method(self, *args):
        assert all(is_term(arg) for arg in args)
        parse_tree = func(self, *args)
        dict_iterator = parse_tree.to_dict_iterator()

        def projection(d):
            return tuple(d[arg] for arg in args if arg.is_var())
        return (projection(d) for d in dict_iterator)
    return resulting_method


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


def _roundrobin(*iterables):
    """Splices the given iterables fairly, see
       http://bugs.python.org/issue1757395
    """
    pending = deque(iter(i).next for i in reversed(iterables))
    rotate, pop, _StopIteration = pending.rotate, pending.pop, StopIteration
    while pending:
        try:
            while 1:
                yield pending[-1]()
                rotate()
        except _StopIteration:
            pop()


