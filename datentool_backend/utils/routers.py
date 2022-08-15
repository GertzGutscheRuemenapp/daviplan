import requests
from django.conf import settings
from routingpy import OSRM


class OSRMRouter():
    def __init__(self, mode):
        self.mode = mode

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

    def _post_service_cmd(self, cmd, **kwargs):
        alias = self.settings['alias']
        return requests.post(f'{self.service_url}/{cmd}/{alias}', **kwargs)

    def run(self):
        res = self._post_service_cmd('run')
        return res.status_code == 200

    def stop(self):
        res = self._post_service_cmd('stop')
        return res.status_code == 200

    def build(self, pbf_path):
        files = {'file': open(pbf_path, 'rb')}
        res = self._post_service_cmd('build', files=files)
        return res.status_code == 200

    def matrix_calculation(self, sources, destinations):
        '''
        sources: list of tuples (lon, lat)
        destinations: list of tuples (lon, lat)
        '''
        client = OSRM(base_url=self.routing_url, timeout=3600)
        coords = sources + destinations
        #radiuses = [30000 for i in range(len(coords))]

        matrix = client.matrix(locations=coords,
                               # radiuses=radiuses,
                               sources=range(len(sources)),
                               destinations=range(len(sources), len(coords)),
                               profile='driving')
        return matrix