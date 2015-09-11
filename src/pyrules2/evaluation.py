from itertools import imap, ifilter, product, islice
from collections import deque, defaultdict
from prolog_like_terms import is_term
from functools import wraps


class RuleBook(object):
    def __init__(self):
        self._parse_trees = dict()
        for method in [method for method in dir(object) if hasattr(method, 'pyrules')]:
            self._register(method)

    def _register(self, method):
        original_method = method.pyrules['original_method']
        virtual_self = None
        args = []
        self._parse_trees[original_method.func_name] = original_method(virtual_self, args)

    def _dispatch(self, method_name, *args):
        parse_tree = self._parse_trees[method_name]
        dict_iterator = parse_tree.to_dict_iterator()

        def projection(d):
            return tuple(d[arg] for arg in args if arg.is_var())
        return (projection(d) for d in dict_iterator)


class _ParseTree(object):
    """
    A _ParseTree represents a program defined using the
    public decorators and functions.
    """

    """
    These are the node types in a parse tree:
    MATCHES: just match the terms to tuples from an iterator
    AND: get results from child trees and return the compatible ones,
         i.e. the ones where a variable has compatible values.
    OR: get results from child trees and return the union of these.
    LIMIT: get the initial results from the child tree.
    """
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
        """
        This is the "code generation" method.
        :return: An iterator of dicts. Each dict maps variables to concrete values.
        """
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
    """
    Example usage:
    @limit(1)
    def p(self, x):
        return matches([atom.A, atom.B], x) # In fact, only x==atom.A will be a solution because of @limit
    :param max_results: The maximum number of results to return, e.g. 200
    :return: A method returning an initial slice of the results provided
    by the decorated method.
    """
    def _limit(method):
        def _resulting_method(self, *args, **kwargs):
            return _ParseTree(
                _ParseTree.LIMIT,
                method(self, *args, **kwargs),
                max_results=max_results)
        return wraps(method)(_resulting_method)
    return _limit


def matches(tuple_iterator, *args):
    """
    Example usage:
    def p(self, x):
        return matches([atom.A, atom.B], x)
    :param tuple_iterator: An iterator of tuples, e.g. [(atom.A, atom.B), (atom.C, atom.D)]
    :param args: A tuple of terms. Each tuple from tuple_iterator must be the same size as args.
    :return: A program that matches the given args every tuple in the iterator.
    """
    # TODO consider better syntactical sugar, e.g. find(x,y).in([...])
    # or something corresponding to reduce(|,match(x,y,foo) for foo in [...])
    # or @rule(style=tuples) def p(x,y): return [...]
    return _ParseTree(
        _ParseTree.MATCHES,
        tuple_iterator=tuple_iterator,
        args=args)


def _dict_iterator_for_matches(tuple_iterator, args):
    var_index_dict = _var_index_dict(args)
    # In case of e.g. self.p(var.x, var.x), match variables
    for var, index_list in var_index_dict.iteritems():
        first_index = index_list[0]
        for other_index in index_list[1:]:
            print other_index
            tuple_iterator = ifilter(lambda t: t[first_index] == t[other_index], tuple_iterator)
    # Match given constants
    for index, arg in enumerate(args):
        if not arg.is_var():
            tuple_iterator = ifilter(lambda t: t[index] == arg, tuple_iterator)

    def tuple_to_dict(t):
        return {v: t[var_index_dict[v][0]] for v in var_index_dict}
    return (tuple_to_dict(t) for t in tuple_iterator)


def rule(func):
    """
    Example usage:
    @rule # Call p like this: for y in r.p(atom.A, var.y): print y
    def p(self, x, y):
        return matches([(atom.A, atom.B), (atom.C, atom.D)], x, y)
    :param func: A method returning a program.
    :return: Solutions
    """
    def resulting_method(self, *args):
        assert all(is_term(arg) for arg in args)
        return self._dispatch(func.func_name, *args)
    new_method_wrapped = wraps(func)(resulting_method)
    new_method_wrapped.pyrules = {'original_method': func}
    return new_method_wrapped


def _var_index_dict(args):
    """
    :param args: A tuple of terms, e.g. (var.x, atom.F, var.x, var.y)
    :return: A dict mapping every occurring variable to the list of indexes
     at which it occurs in args, e.g. {var.x: [0, 2], var.y: [3]}
    """
    d = defaultdict(list)
    for index, arg in enumerate(args):
        if arg.is_var():
            d[arg].append(index)
    return d


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


