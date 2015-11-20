import urllib2
import urllib
import csv
import inspect
from functools import wraps

#  TODO: Consider a syntax like return DBpedia.children(x, y) & DBpedia.children(y, z)

'''
Example:All events in Rome 82 BC
http://dbpedia.org/page/Category:82_BC
http://dbpedia.org/page/Category:Years
http://dbpedia.org/page/Battle_of_the_Colline_Gate_(82_BC)

Notes from earlier, working version:

class World(RuleBook):
    @rule
    @limit(200)
    @wikipedia
    def children(self, parent, child):
        pass

    @rule
    def grandchild(self, x, z, y=LOCAL):
        return self.children(x, y) & self.children(y, z)

    def test_world(self):
        pairs = set(World().grandchild(var.x, var.z))
        self.assertIn((atom.Abd_Manaf_ibn_Qusai, atom.Umayya_ibn_Abd_Shams), pairs)

'''
def wikipedia(func):
    """
    Example usage:
    @wikipedia
    def spouse(self, x, y):
        pass # Magic will go to DBpedia
    :param func: A function a 3 arguments: self + two to match in DBpedia
    :return: A method that matches the two non-self arguments to
     the DBpedia property with the same name as func
    """
    num_args = len(inspect.getargspec(func)[0])
    assert num_args == 3, 'wikipedia predicate must have 3 arguments ("self" plus two), but {} had {}'.format(func.func_name, num_args)

    def resulting_method(self, x, y):
        return matches(_wikipedia_tuples(func.func_name), x, y)
    return wraps(func)(resulting_method)

_PARAMETERS = {'default-graph-uri' : 'http://dbpedia.org',
               'format' : 'text/csv',
               'timeout' : '30000'}
_Q1 = '''select * where {?x <http://dbpedia.org/property/'''
_Q2 = '''> ?y . FILTER (isURI(?y)) } ORDER BY ?x ?y LIMIT 200 OFFSET '''


def _wikipedia_tuples(name):
    index = 0
    while True:
        pars = dict(_PARAMETERS)
        pars['query'] = _Q1 + name + _Q2 + str(index)
        url = 'http://dbpedia.org/sparql?' + urllib.urlencode(pars)
        csv_input = urllib2.urlopen(url, timeout=29)
        count = 0
        for row in csv.DictReader(csv_input):
            count += 1
            try:
                yield (_to_atom(row['x']), _to_atom(row['y']))
            except _NotDBpediaResource:
                pass
        if count < 190:
            break
        index += count


class _NotDBpediaResource(Exception):
    pass

_DBPRES = 'http://dbpedia.org/resource/'


def _to_atom(dbpedia_resource_url):
    parts = dbpedia_resource_url.split(_DBPRES)
    if len(parts) < 2:
        raise _NotDBpediaResource()
    return _Atom(parts[1])

