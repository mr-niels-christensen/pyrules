import inspect
from pyrules2.expression import ReferenceExpression, bind


class VirtualSelf(object):
    pass


class Var(object):
    def __init__(self, name):
        assert isinstance(name, str)
        self.variable_name = name

    def __repr__(self):
        return 'Var({})'.format(self.variable_name)


class ExpressionMethod(object):
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
            elif arg_value is None:
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


def rewrite(rules):
    reference_expressions = {rule_name: ReferenceExpression(rule_name) for rule_name in rules}
    vs = VirtualSelf()
    for rule_name, rule_method in rules.items():
        setattr(vs, rule_name, ExpressionMethod(rule_method, reference_expressions[rule_name]))
    for rule_name, rule_method in rules.items():
        arg_names = inspect.getargspec(rule_method).args
        assert arg_names[0] == 'self'
        vars_for_non_self_args = [Var(arg) for arg in arg_names[1:]]
        generated_expression = rule_method(vs, *vars_for_non_self_args)
        reference_expressions[rule_name].set_expression(generated_expression)
    for rule_name, rule_method in rules.items():
        rules[rule_name] = ExpressionMethod(rule_method, reference_expressions[rule_name])
    # Store an index of the rules
    rules['__index__'] = reference_expressions


class Meta(type):
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
    constructed, every @rule is parsed, i.e. transformed into a _ParseTree.
    The method itself is changed into a call to RuleBook._dispatch()
    """
    __metaclass__ = Meta


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




