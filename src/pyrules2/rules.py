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


class FixedPointMeta(type):
    def __new__(mcs, name, bases, class_dict):
        rules = {key: value for key, value in class_dict.items() if hasattr(value, 'pyrules')}
        rewrite(rules)
        class_dict.update(rules)
        cls = type.__new__(mcs, name, bases, class_dict)
        return cls

    def __str__(self):
        return '\n'.join('{}:\n{}'.format(rule_name, reference_expression.ref) for rule_name, reference_expression in self.__index__.items())


from pyrules2.expression import Expression


class CacheAndTrigger(Expression):
    def __init__(self, name, cache, trigger):
        self.cache = cache
        self.trigger = trigger
        self.name = name

    def __repr__(self):
        return '{}({!r},{!r},{!r})'.format(self.__class__.__name__, self.name, self.cache, self.trigger)

    def scenarios(self):
        for scenario in self.cache:
            yield scenario
        while self.trigger is not None:
            old = self.cache
            done = self.trigger()
            if done:
                return
            added = self.cache - old
            for scenario in added:
                yield scenario


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
        generation_0 = {key: set() for key in self.__class__.__index__}
        self.generations = [generation_0]
        self.backup = {key: ref_expression.ref for key, ref_expression in self.__class__.__index__.items()}
        for key, ref_expression in self.__class__.__index__.items():
            ref_expression.set_expression(CacheAndTrigger(key, set(), self.__next_gen))

    def __next_gen(self):
        current_gen = self.generations[-1]  # Invariant: this is also in the CacheAndTriggers
        next_gen = {key: set() for key in self.__class__.__index__}
        for key, expression in self.backup.items():
            print '{}/{}?'.format(key, len(self.generations))
            self.__add_values(next_gen[key], expression)
            print '{}/{}!'.format(key, len(self.generations))
        fixed_point = all((current_gen[key] == next_gen[key] for key in current_gen))
        if not fixed_point:
            self.generations.append(next_gen)
            for key, scenario_set in next_gen.items():
                self.__class__.__index__[key].ref.cache = scenario_set
        return fixed_point

    def __add_values(self, to_set, expression):
        # Backup refs
        # FIXME this is across all instances and threads!
        # FIXME do not use .ref directly
        backup = {key: ref_expression.ref.trigger for key, ref_expression in self.__class__.__index__.items()}
        # Set refs
        for ref_expression in self.__class__.__index__.values():
            ref_expression.ref.trigger = None
        # Evaluate and add
        for scenario in expression.scenarios():
            to_set.add(scenario)
        # Restore refs
        for key, ref_expression in self.__class__.__index__.items():
            ref_expression.ref.trigger = backup[key]


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




