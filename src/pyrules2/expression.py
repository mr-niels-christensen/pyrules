from pyrules2.scenario import Scenario
from pyrules2.util import lazy_product, round_robin
from types import GeneratorType
from collections import Mapping

__author__ = 'nhc'


class Expression(object):
    """
    Abstract superclass of all Expressions.
    Defines operators that work on Expressions.
    """
    def scenarios(self):
        """
        Must be overridden by all subclasses.
        :returns A generator of Scenarios
        """
        raise NotImplementedError()

    def all_dicts(self):
        """
        Generates every scenario for this Expression as a dict.
        """
        for scenario in self.scenarios():
            yield scenario.as_dict()

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
    An Expression generating exactly one Scenario.
    """
    def __init__(self, mapping):
        """
        Verifies that mapping is a dict and stores a Scenario based on d.
        :param mapping: The single Scenario (as any collections.Mapping) to be generated by this Expression.
        """
        assert isinstance(mapping, Mapping)
        if isinstance(mapping, Scenario):
            self.scenario = mapping
        else:
            self.scenario = Scenario(mapping)

    def scenarios(self):
        """
        :returns A generator yielding a copy of the stored dict.
        """
        yield self.scenario

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.scenario)

    def __str__(self, indent=''):
        return '{}{}({!r})'.format(indent, self.__class__.__name__, self.scenario)


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

    def scenarios(self):
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
    An aggregate Expression which generates one Scenario for each combination
    of Scenarios from its subexpressions when these are compatible (i.e.
    do not define different values for the same key).
    """
    def scenarios(self):
        """
        Yields a number of Scenarios based on this object's subexpressions.
        """
        scenario_generators = (sub_expr.scenarios() for sub_expr in self.subexpressions)
        for prod in lazy_product(*scenario_generators):
            try:
                yield Scenario.unite(prod)
            except AssertionError:
                pass


class OrExpression(AggregateExpression):
    """
    An aggregate Expression which generates every Scenario
     generated by its subexpressions.
    """
    def __or__(self, other):
        assert isinstance(other, Expression)  # TODO: If other is OrExpression, merge
        self.subexpressions.append(other)
        return self

    def scenarios(self):
        """
        Yields all dicts generated by this object's subexpressions.
        """
        iterables = [e.scenarios() for e in self.subexpressions]
        return round_robin(*iterables)


class ReferenceExpression(Expression):
    """
    An Expression which refers to another Expression and generates
    exactly the Scenarios that the referred Expression does.
    The reference can be updated many times.
    """
    def __init__(self, name=None):
        """
        Sets the internal reference to None.
        set_expression() must be called before scenarios() or
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

    def scenarios(self):
        """
        :return: The Scenario generator from the referred Expression.
        :raises AssertionError: if the internal reference is None.
        """
        assert self.ref is not None
        return self.ref.scenarios()

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
    An Expression that generates every Scenario generated by its subexpression
    excepting the ones where a specified key does not map to a specified value.
    """
    def __init__(self, key, expected_value, expr):
        """
        The return Expression will propagate every Scenario s from expr,
        if s.as_dict()[key] == expected_value
        :param key: The key to check, e.g. 'x'
        :param expected_value: The value that key must map to, e.g. 42
        :param expr: The expression generating the Scenarios to check
        :return: A filtered Expression
        """
        self.key = key
        self.expected_value = expected_value
        assert isinstance(expr, Expression)
        self.expr = expr

    def scenarios(self):
        """
        Yields every Scenario generated by this object's subexpression,
        if that Scenario passes the specified filter
        """
        for scenario in self.expr.scenarios():
            if (self.key, self.expected_value) in scenario:
                yield scenario
            else:
                assert self.key in scenario.as_dict()

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
    An Expression that generates at most one Scenario per Scenario generated
    by its subexpression.
    For example, RenameExpression(when(x=0), x='a') generates
      Scenario({'a': 0})
    i.e. the 'x' key is renamed to 'a'.
    When there is a clash between the two values for the same new key, e.g.
      RenameExpression(when(x=0, y=1), x='a', y='a')
    no Scenario is generated, but the process continues, so e.g.
      RenameExpression(when(x=0, y=1) | when(x=0, y=0), x='a', y='a')
    generates one Scenario:
      Scenario({'a': 0})
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

    def scenarios(self):
        """
        :return: Yields one renamed Scenario per Scenario generated by the subexpression,
        but only if there are no clashes.
        """
        for scenario in self.expr.scenarios():
            if len(self.map) == 0:
                yield Scenario({})
            else:
                try:
                    d = scenario.as_dict()
                    new_scenarios = [Scenario({new_key: d[old_key]}) for old_key, new_key in self.map.iteritems()]
                    yield Scenario.unite(new_scenarios)
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
    to values generated by another subexpression.
    E.g. when(f=lambda x: x+2) applied to when(x=0)|when(x=1)
    yields Scenario({'x': 2}) and Scenario({'x': 3}).
    Note that every Scenario generated by the first subexpression
    must contain exactly one value, and that value must be callable.
    Every Scenario, s, generated by the second subexpression must contain
    exactly one value, and that must be a valid argument for every
    callable from the first subexpression.
    If a callable returns a generator, a Scenario will be generated
    per generated value.
    """
    def __init__(self, callable_expression, input_expression):
        """
        :param callable_expression: Subexpression generating callables,
        e.g. when(f=lambda x: x)
        :param input_expression: Subexpression generating input values
        for the above, e.g. when(x=42)
        """
        assert isinstance(callable_expression, Expression)
        self.callable_expression = callable_expression
        assert isinstance(input_expression, Expression)
        self.input_expression = input_expression

    def scenarios(self):
        """
        :return: Yields return values as described above.
        """
        # Each combination of a Scenario from each of the two subexpressions gives rise to one call
        for callable_scenario, \
            input_scenario in lazy_product(self.callable_expression.scenarios(),
                                           self.input_expression.scenarios()):
            # Extract the callable value and the input for the call
            _, callable_value = callable_scenario.get_only_item()
            assert hasattr(callable_value, '__call__')
            key, input_value = input_scenario.get_only_item()
            # Make the call
            returned_value = callable_value(input_value)
            # Output scenario or scenarios (if the returned value was a generator)
            if not isinstance(returned_value, GeneratorType):
                yield Scenario({key: returned_value})
            else:  # It's a generator
                for generated_value in returned_value:
                    yield Scenario({key: generated_value})

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.callable_expression,
                                       self.input_expression)

    def __str__(self, indent=''):
        return '{}{}'.format(indent,
                             self.__class__.__name__) \
               + '\n{}callable:\n{}'.format(indent, self.callable_expression.__str__(indent=indent+'  ')) \
               + '\n{}input:\n{}'.format(indent, self.input_expression.__str__(indent=indent+'  '))
