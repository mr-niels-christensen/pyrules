import inspect
from pyrules2.expression import Expression, bind, IterableWrappingExpression, EMPTY
from functools import partial
from itertools import chain, imap
from collections import Iterable


class Var(object):
    def __init__(self, name):
        assert isinstance(name, str)
        self.variable_name = name

    def __repr__(self):
        return 'Var({})'.format(self.variable_name)


ANYTHING = object()


def _bind_args_to_rule(rule_method, args, expression):
    """
    Translates the call
      rule_method(*args)
    into an Expression, with the given expression representing the body of
    the given rule_method.
    TODO Make this more clear by closer ties to ANYTHING, Var and FixedPointRuleBook.parse
    :param rule_method: A Python function object that used to be the method
     of a RuleBook instance.
    :param args: Suitable arguments for rule_method.
    :param expression: Any Expression.
    :return: An Expression which adds equality constraints to expression
    and picks/renames variables from its scenarios.
    """
    call_args = inspect.getcallargs(rule_method, None, *args)
    assert call_args['self'] is None
    del call_args['self']
    const_bindings = {}
    var_bindings = {}
    for arg_name, arg_value in call_args.iteritems():
        if isinstance(arg_value, Var):
            var_bindings[arg_name] = arg_value.variable_name
        elif arg_value is ANYTHING:
            var_bindings[arg_name] = arg_name
        else:
            const_bindings[arg_name] = arg_value
    return bind(callee_expr=expression,
                callee_key_to_constant=const_bindings,
                callee_key_to_caller_key=var_bindings)


class VirtualMethod(object):
    def __init__(self, rule_method, expression):
        """
        Constructs a callable to replace the given method.
        The callable will generate all dicts for the given expression,
        renamed and filtered using the pyrules.bind() function.
        :param rule_method: A @rule method from a RuleBook
        :param expression: The Expression that will be used
        to represent the body of the rule_method
        :return: The constructed method.
        """
        self.rule_method = rule_method
        assert isinstance(expression, Expression)
        self.expression = expression

    def __call__(self, *args):
        return _bind_args_to_rule(self.rule_method, args, self.expression)

    def __repr__(self):
        return '{}({!r},{!r})'.format(self.__class__.__name__,
                                      self.rule_method,
                                      self.expression)


class RuleBookMethod(object):
    """
    A callable object used to replace rules in a RuleBook.
    This object will call RuleBook.expression_for too get an expression,
    bind the call args using _bind_args_to_rule(), then yield
    all the scenarios from the resulting Expressions.
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, rule_book, *args):
        """
        Note, because of the descriptor protocol, this method will
        not be called directly, but through __get__() below.
        """
        assert isinstance(rule_book, RuleBook)
        unbound_expression = rule_book.expression_for(self.name)
        bound_expression = _bind_args_to_rule(rule_book.rules()[self.name], args, unbound_expression)
        for scenario in bound_expression.scenarios():
            yield scenario.as_dict()

    def __get__(self, instance, instancetype):
        """
        Implementation of the descriptor protocol.
        :return self.__call__ with its first argument bound to the
        RuleBook instance given.
        """
        return partial(self.__call__, instance)


"""Syntactic sugar for RuleBook subclasses.
Add a class variable like this:
    FOOBAR = constant
to define FOOBAR as a constant value containing 'FOOBAR'"""
constant = object()


class RuleBookMeta(type):
    """
    Metaclass for RuleBook.
    Every class with this as a metaclass will be modified in two ways:
      - Every method annotated with @rule is saved in an internal data structure,
        then replaced by a RuleBookMethod.
      - Every variable equal to the object "constant" above will instead
        be assigned to an object containing the variable name.
    """
    def __new__(mcs, name, bases, class_dict):
        rules = {key: value for key, value in class_dict.items() if hasattr(value, 'pyrules')}
        class_dict['__original_rules__'] = rules
        for key in rules:
            class_dict[key] = RuleBookMethod(key)
        for key in class_dict:
            if class_dict[key] == constant:
                class_dict[key] = key
        cls = type.__new__(mcs, name, bases, class_dict)
        return cls


class Generation(object):
    """
    A Generation represents one step in a fixed point computation, see
    https://en.wikipedia.org/wiki/Kleene_fixed-point_theorem
    https://en.wikipedia.org/wiki/Knaster%E2%80%93Tarski_theorem
    """
    def __init__(self, keys):
        self.keys = frozenset(keys)
        self.frozensets = {}
        self.fixed_point = False

    def set(self, key, expression):
        assert isinstance(expression, Expression), '{!r} should have been an Expression'.format(expression)
        assert key in self.keys
        assert key not in self.frozensets
        self.frozensets[key] = frozenset(expression.scenarios())

    def __eq__(self, other):
        assert isinstance(other, Generation)
        assert self.is_full()
        assert other.is_full()
        return self.frozensets == other.frozensets

    def get_expression(self, key):
        assert key in self.frozensets
        return IterableWrappingExpression(self.frozensets[key])

    def as_environment(self):
        return {key: self.get_expression(key) for key in self.keys}

    def fill(self, callback):
        for key in self.keys:
            if key not in self.frozensets:
                self.set(key, callback(key))

    def is_full(self):
        return self.keys == set(self.frozensets.keys())

    def __repr__(self):
        fixed = 'fixedpoint!' if self.fixed_point else '(not known fixedpoint)'
        if self.is_full():
            return '<{} {} full {!r}>'.format(self.__class__.__name__, fixed, self.frozensets)
        else:
            return '<{} {} missing={!r} found={!r}>'.format(self.__class__.__name__, fixed, self.keys.difference(self.frozensets.keys()), self.frozensets)


class DIYIterable(Iterable):
    """
    Utility for constructing an Iterable from an __iter__() function.
    """
    def __init__(self, my_iter):
        self.my_iter = my_iter

    def __iter__(self):
        return self.my_iter()


class RuleBook(object):
    """
    A RuleBook combines a number of rules, i.e. methods decorated with @rule,
    and answers queries to these. When an instance of the RuleBook is
    constructed, every @rule is parsed
    """
    __metaclass__ = RuleBookMeta

    def __init__(self):
        gen0 = Generation(self.rules().keys())
        gen0.fill(lambda key: EMPTY)
        self.generations = [gen0]

    def rules(self):
        return self.__class__.__original_rules__  # TODO: Copy

    def expression_for(self, key):
        def get_scenario_iterator():
            expression_iterator = self._expressions_for(key)
            scenario_iterator = chain.from_iterable(imap(lambda e: e.scenarios(), expression_iterator))
            return scenario_iterator
        scenario_iterable = DIYIterable(get_scenario_iterator)
        return IterableWrappingExpression(scenario_iterable)

    def _expressions_for(self, key):
        current_gen = self.generations[-1]
        yield current_gen.get_expression(key)
        while not current_gen.fixed_point:
            next_gen = self.generations[-1]
            if next_gen == current_gen:
                if not next_gen.fixed_point:
                    self._add_generation()
            else:
                yield next_gen.get_expression(key)
                current_gen = next_gen

    def _add_generation(self):
        last_gen = self.generations[-1]
        next_gen = Generation(self.rules().keys())
        next_gen.fill(lambda key: self.parse(key, last_gen.as_environment()))
        if last_gen == next_gen:
            last_gen.fixed_point = True
        else:
            self.generations.append(next_gen)

    def parse(self, key, environment):
        vs = self.__class__.__new__(self.__class__)
        for rule_name in self.rules():
            setattr(vs, rule_name, VirtualMethod(self.rules()[rule_name],
                                                 environment[rule_name]))
        arg_names = inspect.getargspec(self.rules()[key]).args
        assert arg_names[0] == 'self'
        vars_for_non_self_args = [Var(arg) for arg in arg_names[1:]]
        return self.rules()[key](vs, *vars_for_non_self_args)

    def trace(self, key):
        for i, gen in enumerate(self.generations):
            print '{}@{}: {}'.format(key, i, set(gen.get_expression(key).scenarios()))


def rule(func):
    """
    Example usage:
    @rule # Call p like this: for y in r.p(atom.A, var.y): print y
    def p(self, x, y):
        return matches([(atom.A, atom.B), (atom.C, atom.D)], x, y)
    :param func: A method returning a program.
    :return: Solutions
    """
    func.pyrules = True
    return func




