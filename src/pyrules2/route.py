from collections import namedtuple
from numbers import Number
from frozendict import frozendict
from itertools import permutations, islice
from pyrules2 import when

__author__ = 'nhc'

'''Used as a value in place() below.
Indicates that the named cost is set to 0 when the place is reached.'''
RESET = 'RESET'

'''
Example use: reroute(when(my_var=driving_roundtrip(*MY_PLACES)))
Result is an expression generating scenarios where my_var is mapped
to alternative routes to *MY_PLACES.
Guarantee: If applied recursively, all possible alternatives will be generated.
'''
reroute = when(f=lambda x: x.alternatives())


def limit(**item_limits):
    """
    Creates an Expression to filter scenarios based on numeric bounds.
    Example limit(x=2, y=3)(when(x=1, y=3) | when(x=3, y=0) | when(x=-1, y=4))
     will generate only one Scenario, with {x:1, y:3}.
    :param item_limits: One or more limit on the form some_var=30.
    The returned Expression will remove scenarios where some_var maps to
    values larger than 30.
    :return: An Expression which will filter away scenarios in which
    one or more limit is broken, leaving the remaining unchanged.
    """
    def filter_fun(value):
        bounds_ok = [getattr(value, cost_name) <= lim for cost_name, lim in list(item_limits.items())]
        # Yield either 0 or 1 results
        if all(bounds_ok):
            yield value
    return when(_=filter_fun)


def place(address, **kwargs):
    """
    :param address: A Google Maps compatible string describing the
    location of the place.
    :param kwargs: Any number of named costs associated with this place,
    e.g. tolls_usd=30, stopover_time=5000
    :return: An immutable object representing the place.
    """
    return Place.create(address, **kwargs)


class Place(namedtuple('Place', ['address', 'costs'])):
    """
    Represents one particular stop on a Route.
    When p is a Place,
      - p.address should be a String that Google Maps knows the location of, e.g. "New York".
      - p.costs should be a frozendict mapping from cost name to cost value.
        The cost value must be a number of the value RESET.
        Example: frozendict({'visit_hours': 42, 'coffee': RESET})
    """

    @staticmethod
    def create(address, **kwargs):
        """
        :param address: A Google Maps compatible string describing the
        location of the place.
        :param kwargs: Any number of named costs associated with this place,
        e.g. tolls_usd=30, stopover_time=5000
        :return: An immutable object representing the place.
        """
        assert isinstance(address, str)
        for value in kwargs.values():
            assert value == RESET or isinstance(value, Number)
        return Place(address, frozendict(kwargs))

    def __str__(self):
        return '<{}>'.format(self.address)


class Route(namedtuple('Route', ['places', 'leg_costs'])):
    """
    Represents a sequence of Places to be visited in order.
    The representation includes costs associated with moving from one Place to the next,
    like distance and duration.
    When r is a Route,
      - r.places should be a tuple of Places, e.g. (place('New York'), place('Chicago'), place('Boston'))
      - r.leg_costs should be frozendict mapping from cost name to cost function.
        The cost function should itself be a frozendict mapping each pair of Places in r.places
        to a number.
        Example r.leg_costs:
          frozendict({'distance': di, 'duration': du}), where
          di = du = frozendict({(A,B): 7, (B,A): 8}) where r.places is (A,B)
    """

    def legs(self):
        """
        :return: A list of pairs representing all legs of this Route.
        E.g. if the Route is A->B->C->A the result is [(A,B), (B,C), (C,A)]
        """
        return list(zip(self.places[:-1], self.places[1:]))

    def __getattr__(self, cost_name):
        """
        Convenience method for computing one cost of this Route.
        Example: If every leg in the Route r has a cost named 'distance',
        r.fuel will return sum(l.distance for l in r.legs())
        Example: If every place in the Route r has a cost named 'fuel',
        r.fuel will return max(sum(p.fuel for p in subtrip) for subtrip in r.split(p.fuel==RESET))
        :param cost_name: The name of the cost, e.g. 'fuel'
        :return: the computed cost.
        """
        if cost_name in self.leg_costs:
            return sum([self.leg_costs[cost_name][leg] for leg in self.legs()])
        else:  # Must be per-Place cost
            return max(self._compute_between_resets(cost_name))

    def _compute_between_resets(self, cost_name):
        """
        :param cost_name: Name of a cost, e.g. 'fuel'
        :return: Generator yielding sum(p.fuel for p in subtrip) for subtrip in r.split(p.fuel==RESET)
        """
        current_subtrip = list()
        for stop in self.places:
            value = stop.costs[cost_name]
            if value == RESET:
                if len(current_subtrip) > 0:
                    yield sum(current_subtrip)
                    current_subtrip = []
            else:
                current_subtrip.append(value)
        if len(current_subtrip) > 0:
            yield sum(current_subtrip)

    def __str__(self):
        return '{} km: {}'.format(self.distance / 1000, ' --> '.join(str(p) for p in self.places))

    def alternatives(self):
        """
        Generates every alternative route for this Route.
        :return: Generator yielding Routes with the intermediate stops reordered.
        """
        origin = self.places[0]
        intermediate_stops = self.places[1:-1]
        destination = self.places[-1]
        for alt in islice(permutations(intermediate_stops), 2, None):
            yield Route(places=tuple([origin] + list(alt) + [destination]), leg_costs=self.leg_costs)
