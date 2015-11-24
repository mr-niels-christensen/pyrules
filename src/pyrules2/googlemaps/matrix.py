from collections import namedtuple
from googlemaps import Client

__author__ = 'nhc'


def driving_roundtrip(google_maps_client, *waypoints):
    matrix = google_maps_matrix(google_maps_client, waypoints)
    return Roundtrip(matrix, ())


class Roundtrip(namedtuple('Roundtrip', ['matrix', 'transpositions'])):
    def distance(self):
        order = list(self.matrix.waypoints)
        for index_0, index_1 in self.transpositions:
            tmp = order[index_0]
            order[index_0] = order[index_1]
            order[index_1] = tmp
        trips = zip(order, order[1:] + order[0:1])
        return sum([self.matrix.distance[trip] for trip in trips])


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
    return Matrix(tuple(waypoints), distance, duration)
