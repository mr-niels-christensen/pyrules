from googlemaps import Client

__author__ = 'nhc'


class GoogleMapsMatrix(object):
    def __init__(self, google_maps_client, *waypoints):
        assert isinstance(google_maps_client, Client)
        for waypoint in waypoints:
            assert isinstance(waypoint, basestring)
        self.waypoints = list(waypoints)
        distance = dict()
        duration = dict()
        summary = list()
        response = google_maps_client.distance_matrix(origins=self.waypoints,
                                                      destinations=self.waypoints,
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
                summary.append('{} to {}: {}, {}'.format(origin,
                                                         destination,
                                                         element['duration']['text'],
                                                         element['distance']['text']))
        self.distance = distance
        self.duration = duration
        self.summary = summary

    def __str__(self):
        return '<{}>\n  {}'.format(self.__class__.__name__, '\n  '.join(self.summary))