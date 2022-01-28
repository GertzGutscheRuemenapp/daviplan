from typing import List

import mapbox_vector_tile
from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import BasicModelReadTest

from ..factories import IndicatorFactory

from ..compute import (NumberOfLocations,
                      TotalCapacityInArea,
                      )

from .setup_testdata import CreateInfrastructureTestdataMixin


class TestAreaIndicatorAPI(CreateInfrastructureTestdataMixin,
                           BasicModelReadTest,
                           APITestCase):
    """Test to get an area indicator"""
    url_key = "areaindicators"

    @property
    def query_params(self):
        return {'indicator': self.indicator.pk,
                'area_level': self.area1.area_level.pk, }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.indicator = IndicatorFactory(
            indicator_type__classname=NumberOfLocations.__name__)

        cls = cls.create_areas()
        infrastructure = cls.create_infrastructure_services()
        cls.create_places(infrastructure)
        cls.create_capacities()


    def test_numer_of_places_in_base_scenario(self):
        """Test the number of places with capacity by year for a service"""

        # in the base scenario there should be 2 places in area1
        # and 1 with capacity in area2 for service1
        self.count_capacitites([2, 1], service=self.service1)

        # only 1 in scenario, because capacity of place2 is set to 0
        self.count_capacitites([1, 1], service=self.service1,
                               scenario=self.scenario)
        # ..until 2021
        self.count_capacitites([2, 1], service=self.service1,
                               scenario=self.scenario, year=2022)

        # in the base scenario there should be 1 place in area1 for service2
        self.count_capacitites([1, 0], service=self.service2)
        self.count_capacitites([2, 0], service=self.service2, year=2030)
        self.count_capacitites([2, 0], service=self.service2, year=2035)
        self.count_capacitites([1, 0], service=self.service2,
                               scenario=self.scenario)
        self.count_capacitites([1, 0], service=self.service2,
                               scenario=self.scenario, year=2030)
        self.count_capacitites([2, 0], service=self.service2,
                               scenario=self.scenario, year=2033)
        self.count_capacitites([1, 0], service=self.service2,
                               scenario=self.scenario, year=2035)

        # in 2025-2029 there should be 2 places in area2
        self.count_capacitites([2, 1], service=self.service1, year=2024)

        self.count_capacitites([2, 2], service=self.service1, year=2025)
        self.count_capacitites([2, 2], service=self.service1, year=2029)

        self.count_capacitites([2, 1], service=self.service1, year=2030)
        self.count_capacitites([2, 1], service=self.service1, year=2035)

        # both services
        self.count_capacitites([2, 1], service=[self.service1, self.service2])


    def test_total_capacity(self):
        """Test the number of places with capacity by year for a service"""
        self.indicator = IndicatorFactory(
            indicator_type__classname=TotalCapacityInArea.__name__)

        # service2 has no capacity in place2, should return 0, not None
        self.count_capacitites([2, 0], service=self.service2)
        # in the base scenario there should be 2 places in area1
        # and 1 with capacity in area2 for service1
        self.count_capacitites([5, 44], service=self.service1)
        # both services
        self.count_capacitites([7, 44], service=[self.service1, self.service2])

        # only 1 in scenario, because capacity of place2 is set to 0
        self.count_capacitites([1, 44], service=self.service1,
                               scenario=self.scenario)
        # ..until 2021
        self.count_capacitites([34, 44], service=self.service1,
                               scenario=self.scenario, year=2022)

    def count_capacitites(self,
                       expected_values: List[int],
                       service: int = None,
                       year: int = None,
                       scenario: int = None):
        query_params = {'indicator': self.indicator.pk,
                        'area_level': self.area1.pk, }
        if service is not None:
            if isinstance(service, list):
                query_params['service'] = [s.id for s in service]
            else:
                query_params['service'] = service.id
        if year is not None:
            query_params['year'] = year
        if scenario is not None:
            query_params['scenario'] = scenario.id

        response = self.get_check_200(self.url_key+'-list', data=query_params)
        expected = [{'label': 'area1', 'value': expected_values[0], },
                    {'label': 'area2', 'value': expected_values[1], }]
        self.assert_response_equals_expected(response.data, expected)

    def test_area_tile(self):
        """Test the area_tile for the indicators"""
        area_level = self.obj
        # a tile somewhere in Heegheim in Hessen at zoom-level 13, where the
        # dummy areas are
        url = reverse('layerindicator-tile',
                      kwargs={'pk': area_level.pk,
                              'z': 13, 'x': 4300, 'y': 2767})

        # without indicator in query-params BAD_REQUEST is expected
        response = self.get(url, data={'service': self.service1.pk, })
        self.assert_http_400_bad_request(response)

        #  try the NumberOfLocations indicator
        response = self.get(url, data={'indicator': self.indicator.pk,
                                       'service': self.service1.pk,})
        self.assert_http_200_ok(response)

        #  decode the vector tile returned
        result = mapbox_vector_tile.decode(response.content)
        features = result[area_level.name]['features']
        # the properties contain the values for the areas and the labels
        actual = [feature['properties'] for feature in features]

        expected_values = [2, 1]
        expected = [{'label': 'area1', 'value': expected_values[0], },
                    {'label': 'area2', 'value': expected_values[1], }]
        self.assert_response_equals_expected(actual, expected)

        # Try the TotalCapacityInArea-Indicator
        indicator2 = IndicatorFactory(
            indicator_type__classname=TotalCapacityInArea.__name__)

        # and with some other query-params
        response = self.get(url, data={'indicator': indicator2.pk,
                                       'service': self.service1.pk,
                                       'scenario': self.scenario.pk,
                                       'year': 2022, })
        self.assert_http_200_ok(response)

        result = mapbox_vector_tile.decode(response.content)
        features = result[area_level.name]['features']
        actual = [feature['properties'] for feature in features]
        # the values represent now the total capacity
        # for service and year in scenario
        expected_values = [34, 44]
        expected = [{'label': 'area1', 'value': expected_values[0], },
                    {'label': 'area2', 'value': expected_values[1], }]
        self.assert_response_equals_expected(actual, expected)
