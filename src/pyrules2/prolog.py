
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
        return _dummy_func
    return dummy_decorator

def rule(func):
    return func

class _DummyResult(object):
    def __init__(self):
        self._foo = [('a','b')]

    def __iter__(self):
        return self

    def next(self):
        if len(self._foo) > 0:
            return self._foo.pop()
        else:
            raise StopIteration

    def __and__(self, other):
        return self

    def __or__(self, other):
        return self

def _dummy_func(*args,**kwargs):
    return _DummyResult()



