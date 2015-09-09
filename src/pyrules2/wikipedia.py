import urllib2
import urllib
import csv
import inspect
from prolog_like_terms import _Atom
from evaluation import matches


def wikipedia(func):
    num_args = len(inspect.getargspec(func)[0])
    assert num_args == 3, 'wikipedia predicate must have 3 arguments ("self" plus two), but {} had {}'.format(func.func_name, num_args)

    def resulting_method(self, x, y):
        return matches(_wikipedia_tuples(func.func_name), x, y)
    return resulting_method

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

