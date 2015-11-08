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
        return bind(callee_expr=self.expression,
                    callee_key_to_constant=const_bindings,
                    callee_key_to_caller_key=var_bindings)

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
        seen = set()
        for i in count(1):
            print 'Requesting {}@{}'.format(self.name, i)
            unbound_expression = rule_book.generation(self.name, i)
            bound_expression = self.bind_args_expression(rule_book, args,unbound_expression)
            added = set()
            for scenario in bound_expression.scenarios():
                print '{}: Considering {}'.format(self.name, scenario)
                if scenario not in seen:
                    added.add(scenario)
                    yield scenario.as_dict()
            if len(added) == 0:  # TODO: This should be for all keys, not just this one!
                return
            else:
                seen |= added

    def bind_args_expression(self, rule_book, args, unbound_expression):
        call_args = inspect.getcallargs(rule_book.__class__.__original_rules__[self.name], None, *args)
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
        return bind(callee_expr=unbound_expression,
                    callee_key_to_constant=const_bindings,
                    callee_key_to_caller_key=var_bindings)

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


class FixedPointRuleBook(object):
    """
    A RuleBook combines a number of rules, i.e. methods decorated with @rule,
    and answers queries to these. When an instance of the RuleBook is
    constructed, every @rule is parsed
    """
    __metaclass__ = FixedPointMeta

    def __init__(self):
        pass

    def rules(self):
        return self.__class__.__original_rules__

    def generation(self, key, generation_no):
        assert key in self.rules()
        assert generation_no >= 0
        if generation_no == 0:
            return _EMPTY_EXPRESSION
        previous_generation = {key: self.generation(key, generation_no-1) for key in self.rules()}
        expression_for_key = self.parse(key, previous_generation)
        return expression_for_key

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




