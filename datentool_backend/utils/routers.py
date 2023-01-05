import requests
from django.conf import settings
from routingpy import OSRM
import polyline


class OSRMRouter():
    def __init__(self, mode, algorithm=settings.ROUTING_ALGORITHM):
        self.mode = mode
        self.algorithm = algorithm or 'ch'

    @property
    def settings(self):
        return settings.OSRM_ROUTING[self.mode.name]

    @property
    def service_url(self):
        return f'http://{self.settings["host"]}:{self.settings["service_port"]}'

    @property
    def routing_url(self):
        return f'http://{self.settings["host"]}:{self.settings["routing_port"]}'

    @property
    def service_is_up(self):
        try:
            requests.get(self.service_url)
        except requests.exceptions.ConnectionError:
            return False
        return True

    @property
    def is_running(self):
        try:
            requests.get(self.routing_url)
        except requests.exceptions.ConnectionError:
            return False
        return True

    def _post_service_cmd(self, cmd, data={}, **kwargs):
        alias = self.settings['alias']
        return requests.post(f'{self.service_url}/{cmd}/{alias}', data=data,
                             **kwargs)

    def run(self):
        res = self._post_service_cmd('run', data={'algorithm': self.algorithm })
        return res.status_code == 200

    def stop(self):
        res = self._post_service_cmd('stop')
        return res.status_code == 200

    def remove(self):
        res = self._post_service_cmd('remove')
        return res.status_code == 200

    def build(self, pbf_path: str):
        files = {'file': open(pbf_path, 'rb')}
        res = self._post_service_cmd('build', files=files)
        return res.status_code == 200

    def matrix_calculation(self, sources, destinations):
        '''
        sources: list of tuples (lon, lat)
        destinations: list of tuples (lon, lat)
        '''
        client = OSRMPolyline(base_url=self.routing_url, timeout=3600)
        coords = sources + destinations

        matrix = client.matrix(locations=coords,
                               sources=list(range(len(sources))),
                               destinations=list(range(len(sources), len(coords))),
                               profile='driving')
        return matrix


class OSRMPolyline(OSRM):
    def matrix(
        self,
        locations,
        profile="driving",
        radiuses=None,
        bearings=None,
        sources=None,
        destinations=None,
        dry_run=None,
        annotations=("duration", "distance"),
        **matrix_kwargs,
    ):
        """
        Gets travel distance and time for a matrix of origins and destinations.
        pass the coordinates as polylines
        """
        poly = polyline.encode(locations, geojson=True)
        coords = f'polyline({poly})'

        params = self.get_matrix_params(
            locations, profile, radiuses, bearings, sources, destinations,
            annotations, **matrix_kwargs
        )

        return self.parse_matrix_json(
            self.client._request(f"/table/v1/{profile}/{coords}",
                                 get_params=params, dry_run=dry_run)
        )
