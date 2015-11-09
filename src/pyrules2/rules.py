import inspect
from pyrules2.expression import ReferenceExpression, bind
from itertools import islice
from functools import partial


class VirtualSelf(object):
    pass


class Var(object):
    def __init__(self, name):
        assert isinstance(name, str)
        self.variable_name = name

    def __repr__(self):
        return 'Var({})'.format(self.variable_name)


ANYTHING = object()


class InternalExpressionMethod(object):
    def __init__(self, rule_method, reference_expression):
        """
        Constructs a callable to replace the given method.
        The callable will generate all dicts for the given expression,
        renamed and filtered using the pyrules.bind() function.
        :param rule_method: A @rule method from a RuleBook
        :param reference_expression: The ReferenceExpression that will be used
        to represent the body of the rule_method
        :return: The constructed method.
        """
        self.rule_method = rule_method
        assert isinstance(reference_expression, ReferenceExpression)
        self.reference_expression = reference_expression

    def __call__(self, *args):
        call_args = inspect.getcallargs(self.rule_method, None, *args)
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
        return bind(callee_expr=self.reference_expression,
                    callee_key_to_constant=const_bindings,
                    callee_key_to_caller_key=var_bindings)

    def __repr__(self):
        return '{}({!r},{!r})'.format(self.__class__.__name__,
                                      self.rule_method,
                                      self.reference_expression)


class ExternalExpressionMethod(InternalExpressionMethod):
    """
    Like InternalExpressionMethod, but
      - Does not return the Expression but rather a generator of dicts.
      - Limits the number of results to the page_size attribute
        of the RuleBook.
    Note that ExternalExpressionMethod is a descriptor object.
    This allows it to access the RuleBook object it is member of.
    """
    def __call__(self, rule_book, *args):
        """
        Note, because of the descriptor protocol, this method will
        not be called directly, but through __get__() below.
        """
        expression = super(ExternalExpressionMethod, self).__call__(*args)
        # TODO: Give access to page 2. Workaround: Increase page size.
        assert isinstance(rule_book, RuleBook) or isinstance(rule_book, FixedPointRuleBook)
        return islice(expression.all_dicts(), rule_book.page_size)

    def __get__(self, instance, instancetype):
        """
        Implementation of the descriptor protocol.
        :return self.__call__ with its first argument bound to the
        RuleBook instance given.
        """
        return partial(self.__call__, instance)


def rewrite(rules):
    reference_expressions = {rule_name: ReferenceExpression(rule_name) for rule_name in rules}
    vs = VirtualSelf()
    for rule_name, rule_method in rules.items():
        setattr(vs, rule_name, InternalExpressionMethod(rule_method, reference_expressions[rule_name]))
    for rule_name, rule_method in rules.items():
        arg_names = inspect.getargspec(rule_method).args
        assert arg_names[0] == 'self'
        vars_for_non_self_args = [Var(arg) for arg in arg_names[1:]]
        generated_expression = rule_method(vs, *vars_for_non_self_args)
        reference_expressions[rule_name].set_expression(generated_expression)
    for rule_name, rule_method in rules.items():
        rules[rule_name] = ExternalExpressionMethod(rule_method, reference_expressions[rule_name])
    # Store an index of the rules
    rules['__index__'] = reference_expressions


class StdMeta(type):
    def __new__(mcs, name, bases, class_dict):
        rules = {key: value for key, value in class_dict.items() if hasattr(value, 'pyrules')}
        rewrite(rules)
        class_dict.update(rules)
        cls = type.__new__(mcs, name, bases, class_dict)
        return cls

    def __str__(self):
        return '\n'.join('{}:\n{}'.format(rule_name, reference_expression.ref) for rule_name, reference_expression in self.__index__.items())


class RuleBook(object):
    """
    A RuleBook combines a number of rules, i.e. methods decorated with @rule,
    and answers queries to these. When an instance of the RuleBook is
    constructed, every @rule is parsed.
    """
    __metaclass__ = StdMeta

    def __init__(self):
        # The maximum number of results to generate when calling a rule in this RuleBook
        self.page_size = 1000

from itertools import count
from pyrules2.expression import when, Expression


def _bind_args_to_rule(rule_method, args, expression):
    """
    TODO Make this more clear by closer ties to Var and FixedPointRuleBook.parse
    :param rule_method:
    :param args:
    :param expression:
    :return:
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


class FixedPointMethod(object):  # TODO: AssignableGeneratorMethod?
    """
    TODO
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, rule_book, *args):
        """
        Note, because of the descriptor protocol, this method will
        not be called directly, but through __get__() below.
        """
        assert isinstance(rule_book, FixedPointRuleBook)
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


class FixedPointMeta(type):
    def __new__(mcs, name, bases, class_dict):
        rules = {key: value for key, value in class_dict.items() if hasattr(value, 'pyrules')}
        class_dict['__original_rules__'] = rules
        for key in rules:
            class_dict[key] = FixedPointMethod(key)
        cls = type.__new__(mcs, name, bases, class_dict)
        return cls


class Done(RuntimeError):
    pass


_EMPTY_EXPRESSION = when(x=0) & when(x=1)


class Generation(object):
    def __init__(self, keys):
        self.keys = frozenset(keys)
        self.expressions = {}
        self.frozensets = {}
        self.fixed_point = False

    def set(self, key, expression):
        assert isinstance(expression, Expression), '{!r} should have been an Expression'.format(expression)
        assert key in self.keys
        assert key not in self.expressions
        assert key not in self.frozensets
        self.expressions[key] = expression
        self.frozensets[key] = frozenset(expression.scenarios())

    def __eq__(self, other):
        assert isinstance(other, Generation)
        assert self.is_full()
        assert other.is_full()
        return self.frozensets == other.frozensets

    def get_expression(self, key, callback=None):
        if key not in self.expressions:
            assert callback is not None
            self.set(key, callback(key))
        return self.expressions[key]

    def as_environment(self):
        return self.expressions

    def fill(self, callback):
        for key in self.keys:
            if key not in self.expressions:
                self.set(key, callback(key))

    def is_full(self):
        return self.keys == set(self.expressions.keys())

    def __repr__(self):
        if self.is_full():
            return '<{} full {!r}>'.format(self.__class__.__name__, self.frozensets)
        else:
            return '<{} missing={!r} found={!r}>'.format(self.__class__.__name__, self.keys.difference(self.expressions.keys()), self.frozensets)


class SequentialExpression(Expression):
    def __init__(self, expression_generator):
        self.expression_generator = expression_generator

    def scenarios(self):
        for expression in self.expression_generator:
            assert isinstance(expression, Expression)
            for scenario in expression.scenarios():
                yield scenario


class FixedPointRuleBook(object):
    """
    A RuleBook combines a number of rules, i.e. methods decorated with @rule,
    and answers queries to these. When an instance of the RuleBook is
    constructed, every @rule is parsed
    """
    __metaclass__ = FixedPointMeta

    def __init__(self):
        gen0 = Generation(self.rules().keys())
        gen0.fill(lambda key: _EMPTY_EXPRESSION)
        self.generations = [gen0]

    def rules(self):
        return self.__class__.__original_rules__  # TODO: Copy

    def expression_for(self, key):
        return SequentialExpression(self._expressions_for(key))

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
        vs = VirtualSelf()
        for rule_name in self.rules():
            setattr(vs, rule_name, VirtualMethod(self.rules()[rule_name],
                                                 environment[rule_name]))
        arg_names = inspect.getargspec(self.rules()[key]).args
        assert arg_names[0] == 'self'
        vars_for_non_self_args = [Var(arg) for arg in arg_names[1:]]
        return self.rules()[key](vs, *vars_for_non_self_args)


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




