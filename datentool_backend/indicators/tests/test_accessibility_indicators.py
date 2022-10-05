import pandas as pd
import numpy as np
from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin
from datentool_backend.indicators.views.transit import MatrixCellPlaceViewSet
from datentool_backend.modes.factories import ModeVariantFactory, Mode, ModeVariant
from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.infrastructure.models.places import Capacity
from datentool_backend.population.models import RasterCell
from datentool_backend.user.models.process import ScenarioMode


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
        cls.prepare_population()

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
        ScenarioMode.objects.create(scenario=cls.scenario,
                                    variant=variant)


    def test_max_raster_reachability(self):
        """Test max raster reachability"""

        self.client.force_login(self.profile.user)
        variant = ModeVariant.objects.get(id=self.variant_id)

        query_params = {
            'indicator': 'maxrasterreachability',
            'year': 2022,
            'mode': variant.mode,
            'service': self.service2.pk,
            #'scenario': self.scenario.pk,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data['values']).set_index('cell_code')
        self.assertEquals(len(result), 8)

        # set capacities to 0 for all places except place 5
        capacities_places1_4 = Capacity.objects.exclude(place=self.place5)
        for capacity in capacities_places1_4:
            capacity.capacity = 0
        Capacity.objects.bulk_update(capacities_places1_4, ['capacity'])

        response = self.post(url, data=query_params, extra={'format': 'json'})
        result2 = pd.DataFrame(response.data['values']).set_index('cell_code')
        self.assertEquals(len(result2), 8)

        # for 7 out of 8 rastercells, the traveltime should have increased
        self.assertEqual((result2 > result).sum()[0], 7)
        # and none decreased
        self.assertEqual((result2 < result).sum()[0], 0)

    def test_max_place_reachability(self):
        """Test max place reachability"""

        self.client.force_login(self.profile.user)
        variant = ModeVariant.objects.get(id=self.variant_id)

        query_params = {
            'indicator': 'maxplacereachability',
            'year': 2022,
            'mode': variant.mode,
            'service': self.service2.pk,
            # 'scenario': self.scenario.pk,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data['values']).set_index('place_id')
        self.assertEquals(len(result), 3)

        # set capacities to 0 for all places except place 5
        capacities_places1_4 = Capacity.objects.exclude(place=self.place5)
        for capacity in capacities_places1_4:
            capacity.capacity = 0
        Capacity.objects.bulk_update(capacities_places1_4, ['capacity'])

        response = self.post(url, data=query_params, extra={'format': 'json'})
        result2 = pd.DataFrame(response.data['values']).set_index('place_id')
        self.assertEquals(len(result2), 1)

    def test_average_place_reachability(self):
        """Test average place reachability"""

        self.client.force_login(self.profile.user)
        variant = ModeVariant.objects.get(id=self.variant_id)

        query_params = {
            'indicator': 'averageplacereachability',
            'year': 2022,
            'mode': variant.mode,
            'service': self.service2.pk,
            # 'scenario': self.scenario.pk,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data['values']).set_index('place_id')
        self.assertEquals(len(result), 3)

        # set capacities to 0 for all places except place 5
        capacities_places1_4 = Capacity.objects.exclude(place=self.place5)
        for capacity in capacities_places1_4:
            capacity.capacity = 0
        Capacity.objects.bulk_update(capacities_places1_4, ['capacity'])

        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result2 = pd.DataFrame(response.data['values']).set_index('place_id')
        self.assertEquals(len(result2), 1)

    def test_average_area_reachability(self):
        """Test average area reachability"""

        self.client.force_login(self.profile.user)
        variant = ModeVariant.objects.get(id=self.variant_id)

        query_params = {
            'indicator': 'averageareareachability',
            'year': 2022,
            'mode': variant.mode,
            'service': self.service2.pk,
            'area_level': self.area_level2.pk,
            # 'scenario': self.scenario.pk,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data['values']).set_index('area_id')
        self.assertEquals(len(result), 2)

        # set capacities to 0 for all places except place 5
        capacities_places1_4 = Capacity.objects.exclude(place=self.place5)
        for capacity in capacities_places1_4:
            capacity.capacity = 0
        Capacity.objects.bulk_update(capacities_places1_4, ['capacity'])

        response = self.post(url, data=query_params, extra={'format': 'json'})
        result2 = pd.DataFrame(response.data['values']).set_index('area_id')
        self.assertEquals(len(result2), 2)

        result2 = result2.join(result['value'], lsuffix='_new', rsuffix='_old')
        self.assertTrue((result2['value_new'] > result2['value_old']).all())

    def test_cutoff_area_reachability(self):
        """Test cutoff area reachability"""

        self.client.force_login(self.profile.user)
        variant = ModeVariant.objects.get(id=self.variant_id)

        query_params = {
            'indicator': 'cutoffareareachability',
            'year': 2022,
            'mode': variant.mode,
            'service': self.service2.pk,
            'area_level': self.area_level2.pk,
        }

        query_params['cutoff'] = 6
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result_6 = pd.DataFrame(response.data['values']).set_index('area_id')
        np.testing.assert_array_almost_equal(result_6['value'], [100, 100])

        query_params['cutoff'] = 5
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result_5 = pd.DataFrame(response.data['values']).set_index('area_id')
        np.testing.assert_array_almost_equal(result_5['value'], [22.3, 100])

        query_params['service'] = self.service_uniform.pk
        url = reverse(self.url_key, kwargs={'pk': self.service_uniform.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result_u = pd.DataFrame(response.data['values']).set_index('area_id')
        np.testing.assert_array_almost_equal(result_u['value'], [22.3, 100])

        query_params['service'] = self.service_without_demand.pk
        url = reverse(self.url_key, kwargs={'pk': self.service_without_demand.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result_u = pd.DataFrame(response.data['values']).set_index('area_id')
        np.testing.assert_array_almost_equal(result_u['value'], [0, 0])

    def test_accessible_demand(self):
        """Test accisible demand at places"""

        self.client.force_login(self.profile.user)
        variant = ModeVariant.objects.get(id=self.variant_id)

        query_params = {
            'indicator': 'accessibledemandperplace',
            'year': 2022,
            'mode': variant.mode,
            'service': self.service2.pk,
            # 'scenario': self.scenario.pk,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data['values']).set_index('place_id')
        self.assertEquals(len(result), 3)
        np.testing.assert_array_almost_equal(result['value'],
                                             [1.88, 6.43, 3.05])

        # set capacities to 0 for all places except place 5
        capacities_places1_4 = Capacity.objects.exclude(place=self.place5)
        for capacity in capacities_places1_4:
            capacity.capacity = 0
        Capacity.objects.bulk_update(capacities_places1_4, ['capacity'])

        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result2 = pd.DataFrame(response.data['values']).set_index('place_id')
        self.assertEquals(len(result2), 1)
        # the whole demand now goes to the last remaining place,
        # so it should be the sum of the demand, that was distributed to 3 places before
        np.testing.assert_array_almost_equal(result2['value'],
                                             [result['value'].sum()],
                                             decimal=1)

    def test_reachability_place(self):
        """Test reachability from given place"""

        self.client.force_login(self.profile.user)

        url_key = 'fixedindicators-reachability-place'

        places = MatrixCellPlace.objects.values('place_id').distinct()
        variant = ModeVariant.objects.get(pk=self.variant_id)

        for place in places:
            query_params = {
                'mode': variant.mode,
                'place': place['place_id'],
            }
            url = reverse(url_key)
            response = self.post(url, data=query_params, extra={'format': 'json'})
            self.assert_http_200_ok(response)
            result = pd.DataFrame(response.data['values']).set_index('cell_code')
            self.assertEquals(len(result), 8)

    def test_reachability_cell(self):
        """Test reachability from given cell"""

        self.client.force_login(self.profile.user)

        url_key = 'fixedindicators-reachability-cell'

        cells = MatrixCellPlace.objects.values('cell_id').distinct()
        variant = ModeVariant.objects.get(pk=self.variant_id)

        for cell in cells:
            rastercell = RasterCell.objects.get(pk=cell['cell_id'])
            query_params = {
                'cell_code': rastercell.cellcode,
                'mode': variant.mode,
            }
            url = reverse(url_key)
            response = self.post(url, data=query_params, extra={'format': 'json'})
            self.assert_http_200_ok(response)
            result = pd.DataFrame(response.data['values']).set_index('place_id')
            self.assertEquals(len(result), 5)

    def test_reachability_next_place(self):
        """Test reachability to next place from all cells"""

        self.client.force_login(self.profile.user)

        url_key = 'fixedindicators-reachability-next-place'

        variants = MatrixCellPlace.objects.values('variant_id', 'variant__mode')\
            .distinct()

        for variant in variants:
            query_params = {
                'year': 2022,
                'mode': variant['variant__mode'],
                'services': [self.service2.pk],
                'scenario': self.scenario.pk,
            }
            url = reverse(url_key)
            response = self.post(url, data=query_params, extra={'format': 'json'})
            self.assert_http_200_ok(response)
            result = pd.DataFrame(response.data['values']).set_index('cell_code')
            self.assertEquals(len(result), 8)


        query_params['places'] = [self.place1.pk, self.place2.pk]
        url = reverse(url_key)
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data['values']).set_index('cell_code')
        self.assertEquals(len(result), 8)
