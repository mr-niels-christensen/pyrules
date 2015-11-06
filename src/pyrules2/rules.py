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
        expression = rule_book.__expression_for_name__(self.name)
        # TODO: Give access to page 2. Workaround: Increase page size.
        return islice(self.bind_args_expression(rule_book, args).all_dicts(), rule_book.page_size)

    def bind_args_expression(self, rule_book, args):
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
        return bind(callee_expr=rule_book.__expression_for_name__(self.name),
                    callee_key_to_constant=const_bindings,
                    callee_key_to_caller_key=var_bindings)

    def __get__(self, instance, instancetype):
        """
        Implementation of the descriptor protocol.
        :return self.__call__ with its first argument bound to the
        RuleBook instance given.
        """
        return partial(self.__call__, instance)


def parse(rules):
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
    return reference_expressions


class FixedPointMeta(type):
    def __new__(mcs, name, bases, class_dict):
        rules = {key: value for key, value in class_dict.items() if hasattr(value, 'pyrules')}
        class_dict['__original_rules__'] = rules
        for key in rules:
            class_dict[key] = FixedPointMethod(key)
        cls = type.__new__(mcs, name, bases, class_dict)
        return cls


from pyrules2.expression import Expression


class Done(RuntimeError):
    pass


class CacheAndTrigger(Expression):
    def __init__(self, name, caches, trigger):
        self.caches = caches
        self.trigger = trigger
        self.name = name

    def __repr__(self):
        return '{}({!r},{!r},{!r})'.format(self.__class__.__name__, self.name, self.cache, self.trigger)

    def scenarios(self):
        for scenario_set in self.caches(self.name):
            for scenario in scenario_set:
                yield scenario
        while True:
            try:
                more = self.trigger(self.name)
                for scenario in more:
                    yield scenario
            except Done:
                return


class FixedPointRuleBook(object):
    """
    A RuleBook combines a number of rules, i.e. methods decorated with @rule,
    and answers queries to these. When an instance of the RuleBook is
    constructed, every @rule is parsed
    """
    __metaclass__ = FixedPointMeta

    def __init__(self):
        # The maximum number of results to generate when calling a rule in this RuleBook
        self.page_size = 1000
        generation_0 = {key: set() for key in self.__class__.__original_rules__}
        self.generations = [generation_0]
        self.computing = False
        self.__rewrite__()

    def __expression_for_name__(self, name):
        return self.__caches__[name]

    def __rewrite__(self):
        parsed_rules = parse(self.__class__.__original_rules__)
        self.__caches__ = {key: CacheAndTrigger(key, self.__get_cache_sets__, self.__next_gen) for key in parsed_rules}
        self.__rules_expressions__ = dict()
        for key, reference_expression in parsed_rules.items():
            self.__rules_expressions__[key] = reference_expression.ref
            reference_expression.ref = self.__caches__[key]

    def __get_cache_sets__(self, key):
        for generation in self.generations:
            yield generation[key]

    def __next_gen(self, for_key):
        if self.computing:
            raise Done()
        self.computing = True  # TODO: Thread safety
        next_gen = {key: set() for key in self.__rules_expressions__}
        for key, expression in self.__rules_expressions__.items():
            self.__add_values(next_gen[key], expression)
            for scenario_set in self.__get_cache_sets__(key):
                next_gen[key] -= scenario_set
        fixed_point = all((len(ss) == 0 for ss in next_gen.values()))
        if not fixed_point:
            self.generations.append(next_gen)
        self.computing = False
        if fixed_point:
            raise Done()
        return next_gen[for_key]

    def __add_values(self, to_set, expression):
        # Backup refs
        # TODO this is across all threads
        # Evaluate and add
        for scenario in expression.scenarios():
            to_set.add(scenario)


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




