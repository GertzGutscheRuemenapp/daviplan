import pandas as pd
import numpy as np
import numpy.testing as nptest
from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin
from datentool_backend.indicators.views.transit import MatrixCellPlaceViewSet
from datentool_backend.modes.factories import ModeVariantFactory, Mode
from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.infrastructure.models.places import Capacity

class TestAccessibilityIndicatorAPI(CreateTestdataMixin,
                                    LoginTestCase,
                                    APITestCase):
    """Test to get an area indicator"""
    url_key = "services-compute-indicator"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()

        cls.create_areas()
        cls.create_years_gender_agegroups()
        cls.create_raster_population()
        cls.create_scenario()
        cls.create_population()
        cls.create_infrastructure_services()
        cls.create_demandrates()
        cls.create_places(infrastructure=cls.service1.infrastructure)
        cls.create_capacities()
        cls.create_traveltime_matrix()

        pd.set_option('mode.use_inf_as_na', True)

    @classmethod
    def create_traveltime_matrix(cls):
        """create traveltime matrix between all cells and places"""
        variant = ModeVariantFactory(mode=Mode.WALK)
        mcs = MatrixCellPlaceViewSet()
        df = mcs.calculate_airdistance_traveltimes(variant=variant, max_distance=5000)
        cellplaces = [MatrixCellPlace(**row.to_dict()) for i, row in df.iterrows()]
        MatrixCellPlace.objects.bulk_create(cellplaces)
        cls.variant_id = variant.pk

    def test_max_raster_reachability(self):
        """Test max raster reachability"""

        self.prepare_population()
        self.client.force_login(self.profile.user)

        query_params = {
            'indicator': 'maxrasterreachability',
            'year': 2022,
            'variant': self.variant_id,
            'service': self.service2.pk,
            #'scenario': self.scenario.pk,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('cell_code')
        self.assertEquals(len(result), 8)

        # set capacities to 0 for all places except place 5
        capacities_places1_4 = Capacity.objects.exclude(place=self.place5)
        for capacity in capacities_places1_4:
            capacity.capacity = 0
        Capacity.objects.bulk_update(capacities_places1_4, ['capacity'])

        response = self.post(url, data=query_params, extra={'format': 'json'})
        result2 = pd.DataFrame(response.data).set_index('cell_code')
        self.assertEquals(len(result2), 8)

        # for 7 out of 8 rastercells, the traveltime should have increased
        self.assertEqual((result2 > result).sum()[0], 7)
        # and none decreased
        self.assertEqual((result2 < result).sum()[0], 0)

    def test_max_place_reachability(self):
        """Test max place reachability"""

        self.prepare_population()
        self.client.force_login(self.profile.user)

        query_params = {
            'indicator': 'maxplacereachability',
            'year': 2022,
            'variant': self.variant_id,
            'service': self.service2.pk,
            #'scenario': self.scenario.pk,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('place_id')
        self.assertEquals(len(result), 3)

        # set capacities to 0 for all places except place 5
        capacities_places1_4 = Capacity.objects.exclude(place=self.place5)
        for capacity in capacities_places1_4:
            capacity.capacity = 0
        Capacity.objects.bulk_update(capacities_places1_4, ['capacity'])

        response = self.post(url, data=query_params, extra={'format': 'json'})
        result2 = pd.DataFrame(response.data).set_index('place_id')
        self.assertEquals(len(result2), 1)
