from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase
from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin
from datentool_backend.indicators.models import (MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )

from datentool_backend.modes.factories import (Mode, ModeVariantFactory,
                                               NetworkFactory)


class TestMatrixCreation(CreateTestdataMixin,
                         LoginTestCase,
                         APITestCase):
    """Test to create a matrix"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()
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

