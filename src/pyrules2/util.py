from collections import deque
from itertools import repeat, izip, count, product

__author__ = 'nhc'


def round_robin(*iterables):
    """Splices the given iterables fairly, see
       http://bugs.python.org/issue1757395
    """
    pending = deque(iter(i).next for i in reversed(iterables))
    rotate, pop, _StopIteration = pending.rotate, pending.pop, StopIteration
    while pending:
        try:
            while 1:
                yield pending[-1]()
                rotate()
        except _StopIteration:
            pop()


def lazy_product(*generators):
    tuple_size = len(generators)
    if tuple_size == 0:
        yield ()
        return
    indexed_generators = [izip(repeat(index), g) for index, g in enumerate(generators)]
    fair_generator = round_robin(*indexed_generators)
    enumerated_fair_generator = izip(count(1), fair_generator)
    cache = [list() for _ in range(tuple_size)]  # TODO sets of frozendicts
    for counter, (index, value) in enumerated_fair_generator:
        cache[index].append(value)
        if counter == tuple_size:
            if any([len(l) == 0 for l in cache]):
                return  # Some generator did not deliver a value
        if counter >= tuple_size:  # TODO: Only if value not seen before
            x = list(cache)
            x[index] = [value]
            for t in product(*x):
                yield t
