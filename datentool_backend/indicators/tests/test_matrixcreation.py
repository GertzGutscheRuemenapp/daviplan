from unittest import skipIf
import urllib

from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase
from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin
from datentool_backend.indicators.models import (MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )

from datentool_backend.modes.factories import (Mode, ModeVariantFactory,
                                               NetworkFactory)


def no_connection(host='http://localhost', port=5000, timeout=1):
    try:
        urllib.request.urlopen(f'{host}:{port}', timeout=timeout)
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
        cls.profile.can_edit_basedata = True
        cls.profile.save()
        cls.create_project_settings()
        cls.create_years_gender_agegroups()
        cls.create_raster_population()
        infrastructure = cls.create_infrastructure_services()
        cls.create_places(infrastructure=infrastructure)
        cls.create_stops()

    def test_create_airdistance_matrix(self):
        """Test to create an air distance matrix"""
        network = NetworkFactory()
        walk = ModeVariantFactory(mode=Mode.WALK, network=network)
        car = ModeVariantFactory(mode=Mode.CAR, network=network)

        data = {'variant': walk.pk,
                'drop_constraints': False,
                'speed': 4,
                'max_distance': 500,}

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellPlace.objects.filter(variant=walk.pk).count())

        data = {'variant': car.pk,
                'drop_constraints': False,
                'speed': 20,
                'max_distance': 5000,}

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellPlace.objects.filter(variant=car.pk).count())

        data = {'variant': car.pk,
                'drop_constraints': False,
                'speed': 4,
                'max_distance': 5000,}

        res = self.post('matrixcellstops-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellStop.objects.filter(variant=car.pk).count())

        data = {'variant': car.pk,
                'drop_constraints': False,
                'speed': 4,
                'max_distance': 5000,}

        res = self.post('matrixplacestops-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixPlaceStop.objects.filter(variant=car.pk).count())

    @skipIf(no_connection(port=5002), 'no router for walking running')
    def test_create_routed_walk_matrix(self):
        """Test to create an walk matrix from routing"""
        network = NetworkFactory()
        walk = ModeVariantFactory(mode=Mode.WALK, network=network)

        data = {'variant': walk.pk,
                'drop_constraints': False,
                'air_distance_routing': False,
                'max_distance': 3000,
                }

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellPlace.objects.filter(variant=walk.pk).count())


    @skipIf(no_connection(port=5001), 'no router for bicycle running')
    def test_create_routed_bike_matrix(self):
        """Test to create an bicycle matrix from routing"""
        network = NetworkFactory()
        bike = ModeVariantFactory(mode=Mode.BIKE, network=network)

        data = {'variant': bike.pk,
                'drop_constraints': False,
                'air_distance_routing': False,
                'max_distance': 10000,
                }

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellPlace.objects.filter(variant=bike.pk).count())

    @skipIf(no_connection(port=5000), 'no router for car running')
    def test_create_routed_car_matrix(self):
        """Test to create an car matrix from routing"""
        network = NetworkFactory()
        car = ModeVariantFactory(mode=Mode.CAR, network=network)

        data = {'variant': car.pk,
                'drop_constraints': False,
                'air_distance_routing': False,
                'max_distance': 20000,
                }

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data)
        self.assert_http_202_accepted(res)
        print(res.content)
        print(MatrixCellPlace.objects.filter(variant=car.pk).count())
