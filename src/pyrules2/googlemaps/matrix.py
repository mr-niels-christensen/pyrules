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
        bounds_ok = [getattr(value, cost_name) <= lim for cost_name, lim in item_limits.items()]
        # Yield either 0 or 1 results
        if all(bounds_ok):
            yield value
    return when(_=filter_fun)


def driving_roundtrip(*places):
    """
    :param places: A sequence of Places,
    e.g. (place('New York'), place('Chicago'), place('Los Angeles'))
    :return: An immutable object representing the roundtrip visiting
    the given places in sequence, then returning to the first place,
    e.g. New York -> Chicago -> Los Angeles -> New York
    All distances and durations will be based on driving.
    """
    roundtrip_list = list(places) + [places[0]]
    places_tuple = tuple(p if isinstance(p, Place) else Place(p) for p in roundtrip_list)
    return Route(places=places_tuple, trip_costs=frozendict(google_maps_matrix(places_tuple)))


def place(address, **kwargs):
    return Place.create(address, **kwargs)


class Place(namedtuple('Place', ['address', 'costs'])):
    @staticmethod
    def create(address, **kwargs):
        """
        :param address: A Google Maps compatible string describing the
        location of the place.
        :param kwargs: Any number of named costs associated with this place,
        e.g. tolls_usd=30, stopover_time=5000
        :return: An immutable object representing the place.
        """
        assert isinstance(address, basestring)
        for value in kwargs.itervalues():
            assert value is RESET or isinstance(value, Number)
        return Place(address, frozendict(kwargs))

    def __str__(self):
        return self.address


class Route(namedtuple('Route', ['places', 'trip_costs'])):
    def distance(self):
        """
        :return: The total distance of this Roundtrip, in meters.
        """
        return sum([self.trip_costs['distance'][trip] for trip in self.legs()])

    def duration(self):
        """
        :return: The total duration of this Roundtrip, in seconds.
        """
        return sum([self.trip_costs['duration'][trip] for trip in self.legs()])

    def legs(self):
        """
        :return: A list of pairs representing all legs of this Route.
        E.g. if the Route is A->B->C->A the result is [(A,B), (B,C), (C,A)]
        """
        return zip(self.places[:-1], self.places[1:])

    def __getattr__(self, cost_name):
        """
        Convenience method for computing one cost of this Roundtrip.
        Example: If every place in the Roundtrip r has a cost named 'fuel',
        r.fuel will return max(sum(p.fuel for p in subtrip) for subtrip in r.split(p.fuel==RESET))
        :param cost_name: The name of the cost, e.g. 'fuel'
        :return: the computed cost.
        """
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
        return '{} km: {}'.format(self.distance() / 1000, ' --> '.join(str(p) for p in self.places))

    def alternatives(self):
        """
        Generates every alternative route for this Route.
        :return: Generator yielding Routes with the intermediate stops reordered.
        """
        origin = self.places[0]
        intermediate_stops = self.places[1:-1]
        destination = self.places[-1]
        for alt in islice(permutations(intermediate_stops), 2, None):
            yield Route(places=tuple([origin] + list(alt) + [destination]), trip_costs=self.trip_costs)


def google_maps_matrix(places):
    """
    Looks up distances and durations on Google Maps.
    :param places: An iterable of Places.
    :return: A dict mapping each of 'duration' and 'distance' to
     a frozendict mapping Place pairs to relevant values.
    """
    for waypoint in places:
        assert isinstance(waypoint, Place)
    distance = dict()
    duration = dict()
    # Call Google Maps API
    response = _client_().distance_matrix(origins=[place.address for place in places],
                                          destinations=[place.address for place in places],
                                          mode='driving',
                                          units='metric')
    # Verify and parse response
    assert response['status'] == 'OK'
    rows = response['rows']
    assert len(rows) == len(places)
    # Populate the dicts distance and duration
    for row, origin in zip(rows, places):
        row_elements = row['elements']  # There's also data about exact addresses used
        assert len(row_elements) == len(places)
        for element, destination in zip(row_elements, places):
            assert element['status'] == 'OK'
            duration[(origin, destination)] = element['duration']['value']
            distance[(origin, destination)] = element['distance']['value']
    # Construct and return the dict
    return {'distance': frozendict(distance), 'duration': frozendict(duration)}
