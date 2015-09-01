from uuid import uuid4

class _Namespace(object):
    def __init__(self, ctor):
        self._ctor = ctor

    def __getattr__(self, name):
        return self._ctor(name)

class _NamespaceItem(object):
    def __init__(self, name):
        self._name = name

    def __eq__(self, other):
        return isinstance(other, type(self)) and self._name == other._name

    def __ne__(self, other):
        if not isinstance(other, type(self)):
            return True
        return self._name != other._name

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self._name)

class _Var(_NamespaceItem):
    def __init__(self, name):
        super(_Var, self).__init__('{}_{}'.format(name, str(uuid4()).replace('-','_')))
                
    def is_var(self):
        return True

    def __str__(self):
        return '?{}'.format(self._name)

class _Atom(_NamespaceItem):
    def is_var(self):
        return False

    def __str__(self):
        return 'atom.{}'.format(self._name)

var = _Namespace(_Var)
atom = _Namespace(_Atom)

def is_term(x):
    return isinstance(x, _NamespaceItem)


