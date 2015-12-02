from collections import namedtuple
from googlemaps import Client
from frozendict import frozendict
from itertools import permutations, islice
from os import environ
import googlemaps


__author__ = 'nhc'

try:
    key = environ['GOOGLE_MAPS_API_KEY']
    _client_object = googlemaps.Client(key=key)

    def _client_():
        return _client_object
except KeyError:
    def _client_():
        raise Exception('To use Google Maps, put your API key in the environment variable "GOOGLE_MAPS_API_KEY"')


def driving_roundtrip(*waypoints):
    wp_list = [(wp if isinstance(wp, frozendict) else place(wp)) for wp in waypoints]
    matrix = google_maps_matrix(wp_list)
    return Roundtrip(matrix, tuple(xrange(len(wp_list) - 1)))


_ADDRESS_KEY_ = '_address_'


def place(address, **kwargs):
    kwargs[_ADDRESS_KEY_] = address
    return frozendict(kwargs)


class Roundtrip(namedtuple('Roundtrip', ['matrix', 'order'])):
    def _origin_(self):
        return self.matrix.waypoints[0]

    def _stops_in_canonical_order_(self):
        return self.matrix.waypoints[1:]

    def alternatives(self):
        for p in islice(permutations(xrange(len(self.matrix.waypoints) - 1)), 2, None):
            yield Roundtrip(self.matrix, p)

    def itinerary(self):
        sico = self._stops_in_canonical_order_()
        return [self._origin_()] + [sico[i] for i in self.order] + [self._origin_()]

    def distance(self):
        return sum([self.matrix.distance[trip] for trip in self.trips()])

    def trips(self):
        itinerary = self.itinerary()
        return zip(itinerary[:-1], itinerary[1:])

    def duration(self):
        return sum([self.matrix.duration[trip] for trip in self.trips()])

    def __str__(self):
        return '{} km: {}'.format(self.distance() / 1000, ' --> '.join(self.itinerary()))


class Matrix(namedtuple('Matrix', ['waypoints', 'distance', 'duration'])):
    pass


def google_maps_matrix(waypoints):
    for waypoint in waypoints:
        assert isinstance(waypoint, frozendict)
    distance = dict()
    duration = dict()
    response = _client_().distance_matrix(origins=[wp[_ADDRESS_KEY_] for wp in waypoints],
                                          destinations=[wp[_ADDRESS_KEY_] for wp in waypoints],
                                          mode='driving',
                                          units='metric')
    assert response['status'] == 'OK'
    rows = response['rows']
    assert len(rows) == len(waypoints)
    for row, origin in zip(rows, waypoints):
        row_elements = row['elements']  # There's also data about exact adresses used
        assert len(row_elements) == len(waypoints)
        for element, destination in zip(row_elements, waypoints):
            assert element['status'] == 'OK'
            duration[(origin, destination)] = element['duration']['value']
            distance[(origin, destination)] = element['distance']['value']
    return Matrix(tuple(waypoints), frozendict(distance), frozendict(duration))
