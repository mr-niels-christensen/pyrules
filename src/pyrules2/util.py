from collections import deque
from itertools import repeat, count, product

__author__ = 'nhc'


def round_robin(*iterables):
    """Splices the given iterables fairly, see
       http://bugs.python.org/issue1757395
    """
    pending = deque(iter(i).__next__ for i in reversed(iterables))
    rotate, pop, _StopIteration = pending.rotate, pending.pop, StopIteration
    while pending:
        try:
            while 1:
                yield pending[-1]()
                rotate()
        except _StopIteration:
            pop()


def _enumerated_fair_iterator(iterators):
    """
    Combines iterators into one. Example: with input [['a','b'], ['x','y']]
    the returned iterator is equivalent to
    [(1, (0, 'a')), (2, (1, 'x')), (3, (0, 'b')), (4, (1, 'y'))]
    Each original value is paired with the index of the iterator it came from.
    Each pair is annotated with a serial number independent which generator it came from.
    The iterators are polled using round_robin above.
    :param iterators: Any number of iterators, finite or infinite.
    :return: The combined iterator.
    """
    indexed_iterators = [zip(repeat(index), g) for index, g in enumerate(iterators)]
    fair_iterators = round_robin(*indexed_iterators)
    enumerated_fair_iterators = zip(count(1), fair_iterators)
    return enumerated_fair_iterators


def lazy_product(*iterators):
    """
    Akin to itertools.product except
        - works with infinite iterators
        - does not order the generated tuples in the same way
        - requires every value to be hashable
    For finite iterators, the following should hold:
        set(itertools.product(*iterators)) == set(lazy_product(*iterators))
    :param iterators: Any number of iterators
    :return: One generator that yields tuples. Each tuple contains
    one value from each of the input iterators.
    """
    tuple_size = len(iterators)
    if tuple_size == 0:  # Special case: Just yield the empty tuple
        yield ()
        return
    # General case: Keep a cache of every seen value, per iterator
    cache = [set() for _ in range(tuple_size)]
    # For each new value from one of the iterators...
    for counter, (index, value) in _enumerated_fair_iterator(iterators):
        # Add it to the cache
        seen_before = value in cache[index]
        cache[index].add(value)
        # If every iterator has been polled once and one was empty: Return
        if counter == tuple_size:
            if any([len(l) == 0 for l in cache]):
                return  # Some generator did not deliver a value
        # If every iterator has provided at least one value and this one was new:
        if counter >= tuple_size and not seen_before:
            # Generate every tuple possible using the new value
            x = list(cache)
            x[index] = [value]
            for t in product(*x):
                yield t
