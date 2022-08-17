import pandas as pd
import numpy as np
import numpy.testing as nptest
import unittest

from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from datentool_backend.area.factories import AreaLevelFactory

from .setup_testdata import CreateTestdataMixin
from datentool_backend.demand.models import AgeGroup, Gender
from datentool_backend.area.models import Area, AreaAttribute, AreaLevel
from datentool_backend.population.models import (Population,
                                                 RasterCellPopulation,
                                                 PopulationEntry,
                                                 PopulationAreaLevel, )


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

        pd.set_option('mode.use_inf_as_na', True)

    def test_demand_per_facility(self):
        """Test demand per Facility"""

        self.prepare_population()
        self.client.force_login(self.profile.user)

        query_params = {
            'indicator': 'demandperfacility',
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
        expected = pop['value'] / num_locs['value']
        pd.testing.assert_series_equal(result['value'], expected, check_dtype=False)

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
