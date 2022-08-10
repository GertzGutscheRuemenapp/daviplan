import os
from unittest import skipIf
import urllib
import requests

from test_plus import APITestCase
from django.urls import reverse
from django.conf import settings

from datentool_backend.api_test import LoginTestCase
from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin
from datentool_backend.indicators.models import (MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )

from datentool_backend.modes.factories import (Mode,
                                               ModeVariant,
                                               ModeVariantFactory,
                                               NetworkFactory,
                                               Network)


def no_connection(host: str = 'localhost',
                  port: int = 5000,
                  timeout: float = 1) -> bool:
    """
    try to access host:port with given timeout
    return True, if site is not answering (404, URLError)
    return False, if it is a BadRequest (400)
    """
    try:
        urllib.request.urlopen(f'http://{host}:{port}', timeout=timeout)
        return False
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return True
        return False
    except urllib.error.URLError as err:
        return True
    except Exception as err:
        return True


class TestMatrixCreation(CreateTestdataMixin,
                         LoginTestCase,
                         APITestCase):
    """Test to create a matrix"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        if not no_connection(host=settings.ROUTING_HOST,
                             port=settings.ROUTING_PORT):
            cls.build_osrm()
        cls.profile.can_edit_basedata = True
        cls.profile.save()
        cls.create_project_settings()
        cls.create_years_gender_agegroups()
        cls.create_raster_population()
        infrastructure = cls.create_infrastructure_services()
        cls.create_places(infrastructure=infrastructure)
        cls.create_network()

    def test_create_airdistance_matrix(self):
        """Test to create an air distance matrix"""
        network = self.network
        walk = ModeVariantFactory(mode=Mode.WALK, network=network)
        car = ModeVariantFactory(mode=Mode.CAR, network=network)
        bike = ModeVariantFactory(mode=Mode.BIKE, network=network)

        data = {'variants': [walk.pk, car.pk, bike.pk],
                'drop_constraints': False,
                'air_distance_routing': True, }

        res= self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellPlace.objects.filter(variant=walk.pk).count())
        print(MatrixCellPlace.objects.filter(variant=car.pk).count())
        print(MatrixCellPlace.objects.filter(variant=bike.pk).count())

    def calc_cell_place_matrix(self, mode: ModeVariant, meter: int) -> str:
        """
        calculate the matrix between cells and places
        and return the content of the response
        """
        data = {'variants': mode.pk,
                'drop_constraints': False,
                'max_distance': meter,
                }

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        content = res.content
        return content

    @skipIf(no_connection(host=settings.ROUTING_HOST, port=settings.ROUTING_PORT),
            'osrm docker not running')
    def test_create_routed_walk_matrix(self):
        """Test to create an walk matrix from routing"""
        network = self.network
        walk = ModeVariantFactory(mode=Mode.WALK, network=network)
        content = self.calc_cell_place_matrix(mode=walk, meter=3000)
        print(content)
        print(MatrixCellPlace.objects.filter(variant=walk.pk).count())

    @skipIf(no_connection(host=settings.ROUTING_HOST, port=settings.ROUTING_PORT),
            'osrm docker not running')
    def test_create_routed_bike_matrix(self):
        """Test to create an bicycle matrix from routing"""
        network = self.network
        bike = ModeVariantFactory(mode=Mode.BIKE, network=network)
        content = self.calc_cell_place_matrix(mode=bike, meter=10000)
        print(content)
        print(MatrixCellPlace.objects.filter(variant=bike.pk).count())

    @skipIf(no_connection(host=settings.ROUTING_HOST, port=settings.ROUTING_PORT),
            'osrm docker not running')
    def test_create_routed_car_matrix(self):
        """Test to create an car matrix from routing"""
        network = self.network
        car = ModeVariantFactory(mode=Mode.CAR, network=network)
        content = self.calc_cell_place_matrix(mode=car, meter=20000)
        print(content)
        print(MatrixCellPlace.objects.filter(variant=car.pk).count())

    def get_file_path_stops(self, filename_stops: str = None) -> str:
        return file_path_stops

    @classmethod
    def build_osrm(cls):
        pbf = os.path.join(os.path.dirname(__file__),
                           'testdata', 'projectarea.pbf')
        baseurl = f'http://{settings.ROUTING_HOST}:{settings.ROUTING_PORT}'
        # ToDo: use own route to run and build to test
        for mode in ['car', 'bicycle', 'foot']:
            files = {'file': open(pbf, 'rb')}
            requests.post(f'{baseurl}/build/{mode}', files=files)
            requests.post(f'{baseurl}/run/{mode}')

    @classmethod
    def create_network(cls):
        """create network"""
        cls.network = NetworkFactory()

    def create_stops(self):
        """upload stops from excel-template"""

        self.transit, created = ModeVariant.objects.get_or_create(
            mode=Mode.TRANSIT, network=self.network)

       # upload stops
        file_path_transit = os.path.join(os.path.dirname(__file__),
                                    'testdata',
                                    'transit')
        file_path_stops = os.path.join(file_path_transit,
                                    'Haltestellen_Stockheim.xlsx')
        file_content = open(file_path_stops, 'rb')
        data = {
            'excel_file': file_content,
            'variant': self.transit.pk,
        }

        url = reverse('stops-upload-template')
        res = self.client.post(url, data, extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)

        #  upload traveltime-matrix from stop to stop
        file_path_matrix = os.path.join(file_path_transit,
                                 'Beförderungszeit.mtx')
        file_content = open(file_path_matrix, 'rb')
        data = {
            'excel_or_visum_file': file_content,
            'variant': self.transit.pk,
            'drop_constraints': False,
        }

        url = reverse('matrixstopstops-upload-template')
        res = self.client.post(url, data, extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)

    @skipIf(no_connection(host=settings.ROUTING_HOST, port=settings.ROUTING_PORT),
            'osrm docker not running')
    def test_create_routed_cell_stop_walk_matrix(self):
        """Test to create an walk matrix from cell to stop"""
        network = self.network
        self.create_stops()
        walk, created = ModeVariant.objects.get_or_create(mode=Mode.WALK,
                                                          network=self.network)
        content = self.calc_cell_stop_matrix(mode=walk)
        print(content)
        print(MatrixCellStop.objects.filter(variant=walk.pk).count())

    def calc_cell_stop_matrix(self, mode: ModeVariant) -> str:
        """
        calculate the matrix between cells and stops
        and return the content of the response
        """

        data = {'variants': mode.pk,
                'drop_constraints': False,
                }

        res = self.post('matrixcellstops-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        return res.content

    @skipIf(no_connection(host=settings.ROUTING_HOST, port=settings.ROUTING_PORT),
            'osrm docker not running')
    def test_create_routed_place_stop_walk_matrix(self):
        """Test to create an walk matrix from place to stop"""
        self.create_stops()
        walk, created = ModeVariant.objects.get_or_create(mode=Mode.WALK,
                                                          network=self.network)

        content = self.calc_place_stop_matrix(mode=walk)
        print(content)
        print(MatrixPlaceStop.objects.filter(variant=walk.pk).count())

    def calc_place_stop_matrix(self, mode: ModeVariant) -> str:
        """
        calculate the matrix between cells and stops
        and return the content of the response
        """
        data = {'variants': mode.pk,
                'drop_constraints': False,
                }

        res = self.post('matrixplacestops-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        return res.content

    @skipIf(no_connection(host=settings.ROUTING_HOST, port=settings.ROUTING_PORT),
            'osrm docker not running')
    def test_create_place_cell_transit_matrix(self):
        """Test to create an transit matrix from place to stop"""
        self.create_stops()
        walk, created = ModeVariant.objects.get_or_create(mode=Mode.WALK,
                                                          network=self.network)
        # precalculate the walk time from places and rastercells to stops
        content = self.calc_cell_stop_matrix(mode=walk)
        content = self.calc_place_stop_matrix(mode=walk)
        # until 800 m walk the way, if it's faster, over 600 m always take transit
        content = self.calc_cell_place_matrix(mode=walk, meter=600)

        self.transit
        data = {'variants': self.transit.pk,
                'drop_constraints': False,
                'access_variant': walk.pk,
                }

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellPlace.objects.filter(variant=self.transit.pk).count())

