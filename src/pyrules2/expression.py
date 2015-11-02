from collections import defaultdict
from pyrules2.util import lazy_product, round_robin
from types import GeneratorType

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
        if isinstance(other, OrExpression):
            return other.__or__(self)
        else:
            return OrExpression(self, other)

    def __call__(self, input_expression):
        return ApplyExpression(self, input_expression)


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
        return '{}({!r})'.format(self.__class__.__name__, self.d)

    def __str__(self, indent=''):
        return '{}{}({!r})'.format(indent, self.__class__.__name__, self.d)


def when(**kwargs):
    """
    Syntactic sugar for a ConstantExpression. Example: when(a=0, b=1).
    :param kwargs: Any dict.
    :return: A ConstantExpression yielding the given kwargs.
    """
    return ConstantExpression(kwargs)


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
            assert isinstance(subexpression, Expression), repr(subexpression)
        self.subexpressions = list(subexpressions)

    def all_dicts(self):
        """
        Override this in subclasses.
        """
        raise NotImplementedError

    def __repr__(self):
        return '{}{!r}'.format(self.__class__.__name__, self.subexpressions)

    def __str__(self, indent=''):
        return '{}{}\n'.format(indent, self.__class__.__name__) \
               + '\n'.join([e.__str__(indent=indent + '  ') for e in self.subexpressions])


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
        for prod in lazy_product(*dict_generators):
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
    def __or__(self, other):
        assert isinstance(other, Expression)  # TODO: If other is OrExpression, merge
        self.subexpressions.append(other)
        return self

    def all_dicts(self):
        """
        Yields all dicts generated by this object's subexpressions.
        """
        iterables = [e.all_dicts() for e in self.subexpressions]
        return round_robin(*iterables)


class ReferenceExpression(Expression):
    """
    An Expression which refers to another Expression and generates
    exactly the dicts that the referred Expression does.
    The reference can be updated many times.
    """
    def __init__(self, name=None):
        """
        Sets the internal reference to None.
        set_expression() must be called before all_dicts() or
        the latter will fail.
        """
        self.ref = None
        if name is not None:
            assert isinstance(name, str)
            assert len(name) > 0
        self.name = name

    def set_expression(self, ref):
        """
        Sets the internal reference.
        :param ref: The Expression to refer to.
        :raises: AssertionError if ref is not an Expression.
        """
        assert isinstance(ref, Expression)
        self.ref = ref

    def all_dicts(self):
        """
        :return: The dict generator from the referred Expression.
        :raises AssertionError: if the internal reference is None.
        """
        assert self.ref is not None
        return self.ref.all_dicts()

    def set_name(self, name):
        self.name = name

    def __repr__(self):
        if self.name:
            return '<{} name={!r}>'.format(self.__class__.__name__, self.name)
        else:
            return '<{} ref={!r}>'.format(self.__class__.__name__, self.ref)

    def __str__(self, indent=''):
        if self.name:
            return '{}<{} name={!r}>'.format(indent, self.__class__.__name__, self.name)
        else:
            return '{}<{}>\n{}'.format(indent, self.__class__.__name__, self.ref.__str__(indent=indent+'  '))


class FilterEqExpression(Expression):
    """
    An Expression that generates every dict generated by its subexpression
    exception the ones where a specified key does not map to a specified value.
    """
    def __init__(self, key, expected_value, expr):
        """
        The return Expression will propagate every dict d from expr,
        if d[key] == expected_value
        :param key: The key to check, e.g. 'x'
        :param expected_value: The value that key must map to, e.g. 42
        :param expr: The expression generated the dicts to check
        :return: A filtered Expression
        """
        self.key = key
        self.expected_value = expected_value
        assert isinstance(expr, Expression)
        self.expr = expr

    def all_dicts(self):
        """
        Yields every dict generated by this object's subexpression,
        if that dict passes the specified filter
        """
        for d in self.expr.all_dicts():
            if d[self.key] == self.expected_value:
                yield d

    def __repr__(self):
        return '{}({!r},{!r},{!r})'.format(self.__class__.__name__,
                                           self.key,
                                           self.expected_value,
                                           self.expr)

    def __str__(self, indent=''):
        return '{}<{} {!r}=={}>'.format(indent, self.__class__.__name__, self.name, self.expected_value) \
               + '\n'.format(self.expr.__str__(indent=indent+'  '))


class RenameExpression(Expression):
    """
    An Expression that generates at most one dict per dict generated
    by its subexpression.
    For example, RenameExpression(when(x=0), x='a') generates
      {'a': 0}
    i.e. the 'x' key is renamed to 'a'.
    When there is a clash between the two values for the same new key, e.g.
      RenameExpression(when(x=0, y=1), x='a', y='a')
    no dict is generated, but the process continues, so e.g.
      RenameExpression(when(x=0, y=1) | when(x=0, y=0), x='a', y='a')
    generates one dict:
      {'a': 0}
    """
    def __init__(self, expr, **old_key_to_new_key):
        """
        :param expr: Subexpression, e.g. when(x=0)
        :param old_key_to_new_key: Map fom "old" keys generated by the subexpression
        to "new" keys generated by the returned expression.
        """
        assert isinstance(expr, Expression)
        self.expr = expr
        self.map = old_key_to_new_key

    def all_dicts(self):
        """
        :return: Yields one renamed dict per dict generated by the subexpression,
        but only if there are no clashes.
        """
        for d in self.expr.all_dicts():
            if len(self.map) == 0:
                yield {}
            else:
                try:
                    dicts = [{new_key: d[old_key]} for old_key, new_key in self.map.iteritems()]
                    yield AndExpression.union(dicts)
                except AssertionError:
                    pass

    def __repr__(self):
        return '{}({!r},{!r})'.format(self.__class__.__name__,
                                      self.expr,
                                      self.map)

    def __str__(self, indent=''):
        return '{}<{} {!r}>'.format(indent, self.__class__.__name__, self.map) \
               + '\n{}'.format(self.expr.__str__(indent=indent+'  '))


def bind(callee_expr, callee_key_to_constant, callee_key_to_caller_key):
    """
    Utility for building FilterEqExpression and RenameExpressions
    to work like a function call.
    :param callee_expr: Expression for the body of the called function
    :param callee_key_to_constant: Dict representing bindings to
    constants. For example, to represent f(x=0), this dict would be
    {'x': 0}.
    :param callee_key_to_caller_key: Dict representing bindings to
    variables in the caller. For example, to represent f(x=y), this
    dict would be {'x': 'y'}.
    :return: An Expression on the form
    RenameExpression -> FilterEqExpression -> ... -> FilterEqExpression -> callee_expr
    with one RenameExpression and len(callee_key_to_constant) FilterEqExpressions.
    """
    assert isinstance(callee_expr, Expression)
    assert isinstance(callee_key_to_constant, dict)
    assert isinstance(callee_key_to_caller_key, dict)
    result = callee_expr
    for callee_key, constant in callee_key_to_constant.iteritems():
        result = FilterEqExpression(callee_key, constant, result)
    return RenameExpression(result, **callee_key_to_caller_key)


class ApplyExpression(Expression):
    """
    An Expression that applies values generated by one subexpression
    to dicts generated by another subexpression.
    E.g. when(f=lambda x: x+2) applied to when(x=0)|when(x=1)
    yields {'x': 2} and {'x': 3}.
    Note that every dict generated by the first subexpression
    must contain exactly one value, and that value must be callable.
    Every dict, d, generated by the second subexpression must contain
    exactly one value, and **d must be valid arguments for every
    callable from the first subexpression.
    If a callable returns a generator, a dict will be generated
    per generated value.
    """
    def __init__(self, callable_expression, input_expression):
        """
        :param callable_expression: Subexpression generating callables,
        e.g. when(f=lambda x: x)
        :param input_expression: Subexpression generating input dicts
        for the above, e.g. when(x=42)
        """
        assert isinstance(callable_expression, Expression)
        self.callable_expression = callable_expression
        assert isinstance(input_expression, Expression)
        self.input_expression = input_expression

    def all_dicts(self):
        """
        :return: Yields return values as described above.
        """
        # Each combination of a dict from each of the two subexpressions gives rise to one call
        for callable_dict, input_dict in lazy_product(self.callable_expression.all_dicts(),
                                                      self.input_expression.all_dicts()):
            # Extract the callable value and the input for the call
            assert len(callable_dict) == 1
            callable_value = callable_dict.values().pop()
            assert hasattr(callable_value, '__call__')
            assert len(input_dict) == 1  # TODO: If we allow >1, how is the key specified below?
            # Make the call
            returned_value = callable_value(**input_dict)
            # Output dict or dicts (if the returned value was a generator)
            key = input_dict.keys().pop()
            if not isinstance(returned_value, GeneratorType):
                yield {key: returned_value}
            else:  # It's a generator
                for generated_value in returned_value:
                    yield {key: generated_value}

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.callable_expression,
                                       self.input_expression)

    def __str__(self, indent=''):
        return '{}{}'.format(indent,
                             self.__class__.__name__) \
               + '\n{}callable:\n{}'.format(indent, self.callable_expression.__str__(indent=indent+'  ')) \
               + '\n{}input:\n{}'.format(indent, self.input_expression.__str__(indent=indent+'  '))
