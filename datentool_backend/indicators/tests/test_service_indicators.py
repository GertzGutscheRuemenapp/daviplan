import pandas as pd
import numpy as np

from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin


class TestServiceIndicatorAPI(CreateTestdataMixin,
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
        cls.prepare_population()

        pd.set_option('mode.use_inf_as_na', True)

    def test_demand_per_facility(self):
        """Test demand per Facility"""

        self.client.force_login(self.profile.user)

        query_params = {
            'indicator': 'demandperfacility',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }

        for service_id in [self.service1.pk,
                           self.service_uniform.pk,
                           self.service_without_demand.pk]:
            url = reverse(self.url_key, kwargs={'pk': service_id})
            response = self.post(url, data=query_params, extra={'format': 'json'})
            self.assert_http_200_ok(response)
            result = pd.DataFrame(response.data).set_index('area_id')

            query_params['service'] = service_id

            response = self.post('fixedindicators-demand', data=query_params,
                                 extra={'format': 'json'})
            pop = pd.DataFrame(response.data).set_index('area_id')
            response = self.post('fixedindicators-number-of-locations',
                                 data=query_params, extra={'format': 'json'})
            num_locs = pd.DataFrame(response.data).set_index('area_id')
            expected = pop['value'] / num_locs['value']
            pd.testing.assert_series_equal(result['value'], expected, check_dtype=False)

    def test_facility_per_demand(self):
        """Test Facility per Demand"""

        self.client.force_login(self.profile.user)

        query_params = {
            'indicator': 'facilitiesperdemandinarea',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')

        query_params['service'] = self.service1.pk

        response = self.post('fixedindicators-demand', data=query_params,
                             extra={'format': 'json'})
        pop = pd.DataFrame(response.data).set_index('area_id')
        response = self.post('fixedindicators-number-of-locations',
                             data=query_params, extra={'format': 'json'})
        num_locs = pd.DataFrame(response.data).set_index('area_id')
        expected = num_locs['value'] / pop['value'] * 100
        pd.testing.assert_series_equal(result['value'], expected, check_dtype=False)

        # test the the inverse indicators multiply to 1
        query_params = {
            'indicator': 'demandperfacility',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service1.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result_inv = pd.DataFrame(response.data).set_index('area_id')
        res_both = result.merge(result_inv, right_index=True, left_index=True, suffixes=('_fd', '_df'))
        res_both['mult'] = res_both['value_fd'] * res_both['value_df']
        mult = res_both['mult'].values
        np.testing.assert_allclose(mult[np.isfinite(mult)], 100)

        # test uniform demand rate
        query_params = {
            'indicator': 'demandperfacility',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service_uniform.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')
        np.testing.assert_array_almost_equal(result['value'], [np.NaN, 433.84907495778])

        # test empty demand rate
        url = reverse(self.url_key, kwargs={'pk': self.service_without_demand.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')
        np.testing.assert_array_almost_equal(result['value'], [np.NaN, 0])

    def test_demand_per_capacity(self):
        """Test demand per capacity"""

        self.client.force_login(self.profile.user)

        query_params = {
            'indicator': 'demandpercapacity',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service2.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')

        query_params['service'] = self.service2.pk

        response = self.post('fixedindicators-demand', data=query_params,
                             extra={'format': 'json'})
        pop = pd.DataFrame(response.data).set_index('area_id')
        response = self.post('fixedindicators-capacity', data=query_params,
                             extra={'format': 'json'})
        capacity = pd.DataFrame(response.data).set_index('area_id')
        expected = pop['value'] / capacity['value']
        pd.testing.assert_series_equal(result['value'], expected, check_dtype=False)

        # test uniform demand rate
        query_params = {
            'indicator': 'demandpercapacity',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service_uniform.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')
        np.testing.assert_array_almost_equal(result['value'], [np.NaN, 433.84907495778])

        # test empty demand rate
        url = reverse(self.url_key, kwargs={'pk': self.service_without_demand.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')
        np.testing.assert_array_almost_equal(result['value'], [np.NaN, 0])

    def test_capacity_per_demand(self):
        """Test capacity per demand"""

        self.client.force_login(self.profile.user)

        query_params = {
            'indicator': 'capacityperdemandinarea',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service2.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')

        query_params['service'] = self.service2.pk

        response = self.post('fixedindicators-demand', data=query_params,
                             extra={'format': 'json'})
        pop = pd.DataFrame(response.data).set_index('area_id')
        response = self.post('fixedindicators-capacity', data=query_params,
                             extra={'format': 'json'})
        capacity = pd.DataFrame(response.data).set_index('area_id')
        expected = capacity['value'] / pop['value'] * 100
        pd.testing.assert_series_equal(result['value'], expected, check_dtype=False)

        # test the the inverse indicators multiply to 1
        query_params = {
            'indicator': 'demandpercapacity',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service2.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result_inv = pd.DataFrame(response.data).set_index('area_id')
        res_both = result.merge(result_inv, right_index=True, left_index=True, suffixes=('_fd', '_df'))
        res_both['mult'] = res_both['value_fd'] * res_both['value_df']
        mult = res_both['mult'].values
        np.testing.assert_allclose(mult[np.isfinite(mult)], 100)

        # test uniform demand rate
        query_params = {
            'indicator': 'capacityperdemandinarea',
            'area_level': self.area_level2.pk,
            'year': 2022,
        }
        url = reverse(self.url_key, kwargs={'pk': self.service_uniform.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')
        np.testing.assert_array_almost_equal(result['value'], [0, 0.230494901965])

        # test empty demand rate
        url = reverse(self.url_key, kwargs={'pk': self.service_without_demand.pk})
        response = self.post(url, data=query_params, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        result = pd.DataFrame(response.data).set_index('area_id')
        np.testing.assert_array_equal(result['value'], None)
