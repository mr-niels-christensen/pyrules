from frozendict import frozendict
from os import environ
import googlemaps
from pyrules2.route import Place, Route

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


class Driving(object):
    @staticmethod
    def route(*places):
        """
        :param places: A sequence of Places,
        e.g. (place('New York'), place('Chicago'), place('Los Angeles'), place('New York'))
        :return: An immutable object representing the route visiting
        the given places in sequence,
        e.g. New York -> Chicago -> Los Angeles -> New York
        All distances and durations will be based on driving.
        """
        places_tuple = tuple(p if isinstance(p, Place) else Place(p) for p in places)
        leg_costs = frozendict(_google_maps_leg_costs('driving', places_tuple))
        return Route(places=places_tuple, leg_costs=leg_costs)


def _google_maps_leg_costs(mode, places):
    """
    Looks up distances and durations on Google Maps.
    :param mode: A Google Maps mode, e.g. 'driving'.
    :param places: An iterable of Places.
    :return: A dict mapping each of 'duration' and 'distance' to
     a frozendict mapping Place pairs to relevant values.
    """
    for waypoint in places:
        assert isinstance(waypoint, Place)
    distance = dict()
    duration = dict()
    # Call Google Maps API
    response = _client_().distance_matrix(origins=[p.address for p in places],
                                          destinations=[p.address for p in places],
                                          mode=mode,
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
