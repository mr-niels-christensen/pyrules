from collections import namedtuple
from numbers import Number
from frozendict import frozendict
from itertools import permutations, islice
from os import environ
import googlemaps
from pyrules2 import when

__author__ = 'nhc'

# Read Google Maps API key from environment, and create a client object if the key was there
try:
    key = environ['GOOGLE_MAPS_API_KEY']
    _client_object = googlemaps.Client(key=key)

    def _client_():
        return _client_object
except KeyError:
    def _client_():
        raise Exception('''To use Google Maps with pyrules, put your
Google Maps API key in the environment variable "GOOGLE_MAPS_API_KEY"''')


'''Used as a value in place() below.
Indicates that the named cost is set to 0 when the place is reached.'''
RESET = object()

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
        bounds_ok = [getattr(value, item)(max) <= lim for item, lim in item_limits.items()]
        # Yield either 0 or 1 results
        if all(bounds_ok):
            yield value
    return when(_=filter_fun)


def driving_roundtrip(*waypoints):
    """
    :param waypoints: A sequence of Places,
    e.g. (place('New York'), place('Chicago'), place('Los Angeles'))
    :return: An immutable object representing the roundtrip visiting
    the given places in sequence, then returning to the first place,
    e.g. New York -> Chicago -> Los Angeles -> New York
    All distances and durations will be based on driving.
    """
    wp_list = [(wp if isinstance(wp, Place) else Place(wp)) for wp in waypoints]
    matrix = google_maps_matrix(wp_list)
    return Roundtrip(matrix, tuple(xrange(len(wp_list) - 1)))


def place(address, **kwargs):
    return Place(address, **kwargs)


class Place(object):
    def __init__(self, address, **kwargs):
        """
        :param address: A Google Maps compatible string describing the
        location of the place.
        :param kwargs: Any number of named costs associated with this place,
        e.g. tolls_usd=30, stopover_time=5000
        :return: An immutable object representing the place.
        """
        assert isinstance(address, basestring)
        self.address = address
        for value in kwargs.itervalues():
            assert value is RESET or isinstance(value, Number)
        self.costs = frozendict(kwargs)


class Matrix(namedtuple('Matrix', ['waypoints', 'distance', 'duration'])):
    """
    Substructure of Roundtrip, see documentation below.
    """
    pass


# TODO: Drop 'order' and just keep a tuple of Place objects
# TODO: 'matrix' should be considered a collection of per-trip cost function
class Roundtrip(namedtuple('Roundtrip', ['matrix', 'order'])):
    """
    A Roundtrip object represents the roundtrip visiting
    a number of given Places in sequence, then returning to the first place
    When r is a Roundtrip,
      - r.matrix.waypoints is a tuple of Places.
      - r.matrix.distance is a frozendict, mapping every pair of r.matrix.waypoints elements
        to a numeric distance (in meters)
      - r.matrix.duration is a frozendict, mapping every pair of r.matrix.waypoints elements
        to a numeric duration (in seconds)
      - r.order is a tuple of numbers which must be a permutation of 0, 1, ..., len(r.matrix.waypoints)-1
        The full roundtrip of r is r.matrix.waypoints[0] + _reordered + r.matrix.waypoints[0] where
        _reordered = [r.matrix.waypoints[i+1] for i in r.order]
    """
    def _origin_(self):
        """
        :return: The origin (and also final destination) of this Roundtrip.
        """
        return self.matrix.waypoints[0]

    def _stops_in_canonical_order_(self):
        """
        :return: If roundtrip is A->B->C->A result will be [B,C].
        """
        return self.matrix.waypoints[1:]

    def alternatives(self):
        """
        Generates every alternative route for this Roundtrip.
        :return: Generator yielding Roundtrips with the intermediate stops reordered.
        """
        for p in islice(permutations(xrange(len(self.matrix.waypoints) - 1)), 2, None):
            yield Roundtrip(self.matrix, p)

    def itinerary(self):
        """
        :return: The full roundtrip as a list, e.g. [A, B, C, A]
        """
        sico = self._stops_in_canonical_order_()
        return [self._origin_()] + [sico[i] for i in self.order] + [self._origin_()]

    def distance(self):
        """
        :return: The total distance of this Roundtrip, in meters.
        """
        return sum([self.matrix.distance[trip] for trip in self.trips()])

    def trips(self):
        """
        :return: A list of pairs representing all legs of this Roundtrip.
        E.g. if the roundtrip is A->B->C->A the result is [(A,B), (B,C), (C,A)]
        """
        itinerary = self.itinerary()
        return zip(itinerary[:-1], itinerary[1:])

    def duration(self):
        """
        :return: The total duration of this Roundtrip, in meters.
        """
        return sum([self.matrix.duration[trip] for trip in self.trips()])

    def __getattr__(self, cost_name):
        """
        Convenience method for computing one cost of this Roundtrip.
        Example: If every place in the Roundtrip r has a cost named 'fuel',
        r.fuel(max) will return max(sum(p.fuel for p in subtrip) for subtrip in r.split(p.fuel==RESET))
        :param cost_name: The name of the cost, e.g. 'fuel'
        :return: A function which, given either max or sum, returns the computed cost.
        """
        def f(sum_or_max):
            # TODO: Does sum make sense? Wouldn't this be the same for any route?
            assert sum_or_max in [sum, max]
            return self._compute(sum_or_max, cost_name)
        return f

    def _compute(self, sum_or_max, cost_name):
        """

        :param sum_or_max: Must be builtin functions sum or max
        :param cost_name: Name of a cost, e.g. 'fuel'
        :return: Computed cost for this Roundtrip.
        """
        return sum_or_max(self._compute_between_resets(cost_name))

    def _compute_between_resets(self, cost_name):
        """
        :param cost_name: Name of a cost, e.g. 'fuel'
        :return: Generator yielding e.g. sum(p.fuel for p in subtrip) for subtrip in r.split(p.fuel==RESET)
        """
        current_subtrip = list()
        for stop in self.itinerary():
            value = stop.costs[cost_name]
            if value == RESET:
                if len(current_subtrip) > 0:
                    yield sum(current_subtrip)
                    current_subtrip = []
            else:
                assert isinstance(value, Number), 'Not a number: {}[{}]=={}'.format(stop, cost_name, value)
                current_subtrip.append(value)
        if len(current_subtrip) > 0:
            yield sum(current_subtrip)

    def __str__(self):
        return '{} km: {}'.format(self.distance() / 1000, ' --> '.join(self.itinerary()))


def google_maps_matrix(waypoints):
    """
    Looks up distances and durations on Google Maps.
    :param waypoints: An iterable of Places.
    :return: A Matrix for a Roundtrip based on the given waypoints.
    """
    for waypoint in waypoints:
        assert isinstance(waypoint, Place)
    distance = dict()
    duration = dict()
    # Call Google Maps API
    response = _client_().distance_matrix(origins=[wp.address for wp in waypoints],
                                          destinations=[wp.address for wp in waypoints],
                                          mode='driving',
                                          units='metric')
    # Verify and parse response
    assert response['status'] == 'OK'
    rows = response['rows']
    assert len(rows) == len(waypoints)
    # Populate the dicts distance and duration
    for row, origin in zip(rows, waypoints):
        row_elements = row['elements']  # There's also data about exact addresses used
        assert len(row_elements) == len(waypoints)
        for element, destination in zip(row_elements, waypoints):
            assert element['status'] == 'OK'
            duration[(origin, destination)] = element['duration']['value']
            distance[(origin, destination)] = element['distance']['value']
    # Construct and return a Matrix object
    return Matrix(tuple(waypoints), frozendict(distance), frozendict(duration))
