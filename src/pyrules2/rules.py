import inspect
from pyrules2.expression import ConstantExpression, Expression, bind, IterableWrappingExpression, EMPTY
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
person = ANYTHING
anything = ANYTHING


def no(variable):
    """
    Syntactic sugar to bind a variable to None when it is not needed.
    :param variable: An instance of Var.
    :return: An Expression binding the variable name to None.
    """
    assert isinstance(variable, Var)
    return ConstantExpression({variable.variable_name: None})


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
        bound_expression = _bind_args_to_rule(rule_book.rules[self.name], args, unbound_expression)
        for scenario in bound_expression.scenarios():
            yield scenario.as_dict()

    def __get__(self, instance, _instancetype):
        """
        Implementation of the descriptor protocol.
        :return self.__call__ with its first argument bound to the
        RuleBook instance given.
        """
        return partial(self.__call__, instance)


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
            if class_dict[key] == ANYTHING:
                class_dict[key] = key
        cls = type.__new__(mcs, name, bases, class_dict)
        return cls


class Generation(object):
    """
    A Generation represents one step in a fixed point computation, see
    https://en.wikipedia.org/wiki/Kleene_fixed-point_theorem
    https://en.wikipedia.org/wiki/Knaster%E2%80%93Tarski_theorem

    Each Generation instance maps every function name to a frozenset
    of the Scenarios (i.e. outputs) found so far. Every iteration
    will fill a new Generation instance.
    """
    def __init__(self, keys):
        self.keys = frozenset(keys)
        self.frozensets = {}
        self.fixed_point = False

    def set(self, key, expression):
        """
        Assigns a frozenset of Scenarios to one function name.
        Retrieves and stores all Scenarios generated by the given Expression.
        :param key: The function name to map, e.g. 'f'
        :param expression: An Expression that generates all the Scenarios
        for key in this Generation, e.g. when(x=0)
        """
        assert isinstance(expression, Expression), '{!r} should have been an Expression'.format(expression)
        assert key in self.keys
        assert key not in self.frozensets
        self.frozensets[key] = frozenset(expression.scenarios())

    def __eq__(self, other):
        """
        :return True if and only if both objects are full Generations
        and the frozenset of Scenarios agree for every function name.
        """
        assert isinstance(other, Generation)
        assert self.is_full()
        assert other.is_full()
        return self.frozensets == other.frozensets

    def get_expression(self, key):
        """
        :param key: The name of a function, e.g. 'f'.
        :return An Expression that generates the Scenarios for key
        in this Generation.
        """
        assert key in self.frozensets
        return IterableWrappingExpression(self.frozensets[key])

    def as_environment(self):
        """
        Provides an environment for computing the next iteration step
        of the fixed-point computation.
        :return A dict mapping every function name to an expression.
        The expression generates all Scenarios for the function
        in this Generation.
        """
        assert self.is_full()
        return {key: self.get_expression(key) for key in self.keys}

    def fill(self, callback):
        """
        Computes one
        :param callback: A one-argument callback mapping each function name
        to an Expression that generates Scenarios for that function.
        Example: lambda fname: when(x=0)
        """
        for key in self.keys:
            if key not in self.frozensets:
                self.set(key, callback(key))

    def is_full(self):
        """
        :return True if and only if every function name (from the __init__
        argument 'keys') is mapped to a frozenset of Scenarios.
        """
        return self.keys == set(self.frozensets.keys())

    def __repr__(self):
        fixed = 'fixedpoint!' if self.fixed_point else '(not known fixedpoint)'
        if self.is_full():
            return '<{} {} full {!r}>'.format(self.__class__.__name__, fixed, self.frozensets)
        else:
            return '<{} {} missing={!r} found={!r}>'.format(self.__class__.__name__,
                                                            fixed,
                                                            self.keys.difference(self.frozensets.keys()),
                                                            self.frozensets)


class DIYIterable(Iterable):
    """
    Utility for constructing an Iterable from an __iter__() function.
    If you know a clever way of doing this with just the standard library,
    let me know!
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
        """
        Creates and stores the initial Generation of the fixed-point
        iteration (see Generation above).
        """
        self.rules = self.__class__.__original_rules__.copy()
        gen0 = Generation(self.rules.keys())
        gen0.fill(lambda key: EMPTY)
        self.generations = [gen0]

    def expression_for(self, key):
        """
        Internal entry point for getting scenarios for a rule.
        The returned Expression will lazily evaluate steps in the
        fixed-point iteration, see Generation above.
        :param key: The name of a rule in this RuleBook, e.g. 'f'.
        :return An Expression generating every Scenario for the given rule.
        """
        # Define an __iter__ function that calls _expressions_for, extracts scenarios and chains these
        def get_scenario_iterator():
            expression_iterator = self._expressions_for(key)
            scenario_iterator = chain.from_iterable(imap(lambda e: e.scenarios(), expression_iterator))
            return scenario_iterator
        # Make the __iter__ function into an Expression via an Iterable
        scenario_iterable = DIYIterable(get_scenario_iterator)
        return IterableWrappingExpression(scenario_iterable)

    def _expressions_for(self, key):
        """
        :param key: The name of a rule in this RuleBook, e.g. 'f'.
        :return A generator yielding Expressions. The sets Scenarios generated
         by the Expressions will overlap. To get all Scenarios generated
         by a rule, you need to take every Scenario generated by one of the
         yielded Expressions.
        """
        # First: Yield from the latest generation we have
        current_gen = self.generations[-1]
        yield current_gen.get_expression(key)
        # Then: While we have not reached a fixed point
        while not current_gen.fixed_point:
            # Check if someone computed a new Generation
            next_gen = self.generations[-1]
            if next_gen == current_gen:
                # No? Then we have to compute one and try again
                if not next_gen.fixed_point:
                    self._add_generation()
                    # Note: In the next loop, this new generation will turn up in the branch below
            else:
                # Yes? Yield from that and try again
                yield next_gen.get_expression(key)
                current_gen = next_gen

    def _add_generation(self):
        """
        Computes one step of the fixed-point iteration and appends it
        to self.generations.
        """
        last_gen = self.generations[-1]
        next_gen = Generation(self.rules.keys())
        next_gen.fill(lambda key: self.parse(key, last_gen.as_environment()))
        if last_gen == next_gen:
            last_gen.fixed_point = True
        else:
            self.generations.append(next_gen)

    def parse(self, key, environment):
        """
        Parses the rule for key, replacing every call to another rule
        (including recursive calls to the same rule) with the Expression
        for it in the given environment.
        This allows you to get a small Expression representing
        "Which Scenarios would f generate, assuming calls to f and g
        generates these Scenarios?".
        This representation is useful for computing least fixed point
        iterations, see Generation above.
        :param key: The name of a rule in this RuleBook, e.g. 'f'.
        :param environment: A dict mapping from rule names to Expressions,
        e.g. {'f': when(x=0)}
        """
        # Create a virtual "self" object to represent a RuleBook for the given environment
        virtual_self = self.__class__.__new__(self.__class__)
        for rule_name in self.rules:
            setattr(virtual_self,
                    rule_name,
                    VirtualMethod(self.rules[rule_name],
                                  environment[rule_name]))
        # Create an abstract variable for each non-self argument required
        arg_names = inspect.getargspec(self.rules[key]).args
        assert arg_names[0] == 'self'
        vars_for_non_self_args = [Var(arg) for arg in arg_names[1:]]
        # Call the rule method with the constructed arguments and return its result
        return self.rules[key](virtual_self, *vars_for_non_self_args)

    def trace(self, key):
        """
        Print out info on the fixed-point computation for the given rule.
        :param key: The name of a rule in this RuleBook, e.g. 'f'.
        """
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




