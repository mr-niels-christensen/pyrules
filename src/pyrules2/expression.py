from collections import defaultdict, deque
from itertools import imap, ifilter, product

__author__ = 'nhc'


class Expression(object):
    """
    Abstract superclass of all Expressions.
    Defines operators that work on Expressions.
    """
    def all_dicts(self):
        """
        Must be overridden by all subclasses.
        """
        raise NotImplementedError

    def __and__(self, other):
        """
        :returns An AndExpression combining self and other.
        """
        return AndExpression(self, other)

    def __or__(self, other):
        """
        :returns An OrExpression combining self and other.
        """
        return OrExpression(self, other)


class ConstantExpression(Expression):
    """
    An Expression generating exactly one dict.
    """
    def __init__(self, d):
        """
        Verifies that d is a dict and stores a copy of d.
        :param d: The single dict to be generated by this Expression.
        """
        assert isinstance(d, dict)
        self.d = d.copy()

    def all_dicts(self):
        """
        :returns A generator yielding a copy of the stored dict.
        """
        yield self.d.copy()

    def __repr__(self):
        return '{}({!r})'.format(self.__class__, self.d)


def when(**kwargs):
    """
    Syntactic sugar for a ConstantExpression. Example: when(a=0, b=1).
    :param kwargs: Any dict.
    :return: A ConstantExpression yielding the given kwargs.
    """
    return ConstantExpression(kwargs)


class CallExpression(Expression):
    def __init__(self, rule_name):
        self.rule_name = rule_name

    def all_dicts(self, rule_book):
        return rule_book.expression_for_name(self.rule_name).all_dicts(rule_book)


class ArgHandlerExpression(Expression):
    def __init__(self, rule_name, index, concrete_arg, sub_expression):
        self.rule_name = rule_name
        self.index = index
        self.concrete_arg = concrete_arg
        self.sub_expression = sub_expression

    def all_dicts(self, rule_book):
        abstract_arg = rule_book.args_for_name(self.rule_name)[self.index]
        for d in self.sub_expression.all_dicts(rule_book):
            returned_value = d[abstract_arg]
            if self.concrete_arg.is_var():
                yield {self.concrete_arg : returned_value}
            else:
                if self.concrete_arg == returned_value:
                    yield dict()


class KwargHandlerExpression(Expression):
    def __init__(self, abstract_arg, concrete_arg, sub_expression):
        self.abstract_arg = abstract_arg
        self.concrete_arg = concrete_arg
        self.sub_expression = sub_expression

    def all_dicts(self, rule_book):
        for d in self.sub_expression.all_dicts(rule_book):
            returned_value = d[self.abstract_arg]
            if self.concrete_arg.is_var():
                yield {self.concrete_arg : returned_value}
            else:
                if self.concrete_arg == returned_value:
                    yield dict()


def expr_call(rule_name, concrete_args, concrete_kwargs):
    call = CallExpression(rule_name)
    arg_handlers = [ArgHandlerExpression(rule_name, index, concrete_arg, call)
                    for index, concrete_arg in enumerate(concrete_args)]
    kwarg_handlers = [KwargHandlerExpression(abstract_arg, concrete_arg, call)
                      for abstract_arg, concrete_arg in concrete_kwargs.iteritems()]
    return AndExpression(*(arg_handlers + kwarg_handlers))


class AggregateExpression(Expression):
    """
    An aggregate Expression, i.e. one that combines subexpressions.
    This is an abstract superclass of OrExpression and AndExpression.
    """
    def __init__(self, *subexpressions):
        """
        Stores the given subexpressions after verifying that each is
        an Expression instance.
        :param subexpressions: The subexpression to aggregate.
        """
        for subexpression in subexpressions:
            assert isinstance(subexpression, Expression)
        self.subexpressions = subexpressions

    def all_dicts(self):
        """
        Override this in subclasses.
        """
        raise NotImplementedError

    def __repr__(self):
        return '{}{!r}'.format(self.__class__, self.subexpressions)


class AndExpression(AggregateExpression):
    """
    An aggregate Expression which generates one dict for each combination
    of dicts from its subexpressions when these are compatible (i.e.
    do not define different values for the same key).
    """
    def all_dicts(self):
        """
        Yields a number of dicts based on this object's subexpressions.
        """
        dict_generators = (sub_expr.all_dicts() for sub_expr in self.subexpressions)
        for prod in product(*dict_generators):
            try:
                yield AndExpression.union(prod)
            except AssertionError:
                pass

    @staticmethod
    def union(dicts):
        """
        :param dicts A tuple or list of dicts, e.g. ({0: 1},{'a':'b'}).
        :return The union of the dicts, e.g. {'a': 'b', 0: 1}.
        :raises AssertionError if two dicts defined different values for
        the same key.
        """
        assert len(dicts) > 0
        accumulator = defaultdict(set)
        for d in dicts:
            for key in d:
                accumulator[key].add(d[key])
        result = dict()
        for key, value_set in accumulator.iteritems():
            assert len(value_set) == 1
            result[key] = value_set.pop()
        return result


class OrExpression(AggregateExpression):
    """
    An aggregate Expression which generates every dict
     generated by its subexpressions.
    """
    def all_dicts(self):
        """
        Yields all dicts generated by this object's subexpressions.
        """
        iterables = [e.all_dicts() for e in self.subexpressions]
        return OrExpression.round_robin(*iterables)

    @staticmethod
    def round_robin(*iterables):
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


