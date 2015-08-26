
class RuleBook(object):
    pass

class _Namespace(object):
    def __getattr__(self, name):
        if name.startswith("__"):  # ignore any special Python names!
            raise AttributeError
        else:
            return None

var = _Namespace

