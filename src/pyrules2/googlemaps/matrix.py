from collections import namedtuple
from googlemaps import Client
from frozendict import frozendict
from itertools import permutations, islice


__author__ = 'nhc'


def driving_roundtrip(google_maps_client, *waypoints):
    matrix = google_maps_matrix(google_maps_client, waypoints)
    return Roundtrip(matrix, tuple(xrange(len(waypoints) - 1)))


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
        itinerary = self.itinerary()
        trips = zip(itinerary[:-1], itinerary[1:])
        return sum([self.matrix.distance[trip] for trip in trips])

    def __str__(self):
        return '{} km: {}'.format(self.distance() / 1000, ' --> '.join(self.itinerary()))


class Matrix(namedtuple('Matrix', ['waypoints', 'distance', 'duration'])):
    pass


def google_maps_matrix(google_maps_client, waypoints):
    assert isinstance(google_maps_client, Client)
    for waypoint in waypoints:
        assert isinstance(waypoint, basestring)
    distance = dict()
    duration = dict()
    response = google_maps_client.distance_matrix(origins=list(waypoints),
                                                  destinations=list(waypoints),
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
