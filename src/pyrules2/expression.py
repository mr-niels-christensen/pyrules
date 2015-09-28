from itertools import imap, ifilter, product
from collections import deque

__author__ = 'nhc'


class Expression(object):
    def all_dicts(self):
        pass

    def __and__(self, other):
        return AndExpression(self, other)

    def __or__(self, other):
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
        self.d = dict(d)

    def all_dicts(self):
        yield self.d


def when(**kwargs):
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


class AndExpression(Expression):
    def __init__(self, *sub_expressions):
        self.sub_expressions = sub_expressions

    def all_dicts(self):
        dict_generators = (sub_expr.all_dicts() for sub_expr in self.sub_expressions)
        return imap(AndExpression.union,
                    ifilter(AndExpression.compatible,
                            product(*dict_generators)))

    @staticmethod
    def union(dict0, dict1):
        d = dict0.copy()
        d.update(dict1)
        return d

    @staticmethod
    def compatible(dict0, dict1):
        for key in dict0:
            if key in dict1 and dict0[key] != dict1[key]:
                return False
        return True


class OrExpression(Expression):
    def __init__(self, *subexpressions):
        self.sub_expressions = subexpressions

    def all_dicts(self):
        iterables = [e.all_dicts() for e in self.sub_expressions]
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


