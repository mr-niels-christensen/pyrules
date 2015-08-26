
class RuleBook(object):
    pass

class _Namespace(object):
    def __getattr__(self, name):
        if name.startswith("__"):  # ignore any special Python names!
            raise AttributeError
        else:
            return 'atom.{}'.format(name)

var = _Namespace()
atom = _Namespace()

def pairs(pairs_iterator):
    def dummy_decorator(func):
        return func
    return dummy_decorator

def rule(func):
    return func


