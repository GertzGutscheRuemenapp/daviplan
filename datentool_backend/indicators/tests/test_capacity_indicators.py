from typing import List
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase, BasicModelCompareMixin
from .setup_testdata import CreateTestdataMixin


class TestAreaIndicatorAPI(CreateTestdataMixin,
                           LoginTestCase, BasicModelCompareMixin, APITestCase):
    """Test to get an area indicator"""
    url_key = "fixedindicators"

    @property
    def query_params(self):
        return {'area_level': self.area1.area_level.pk, }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()

        cls = cls.create_areas()
        infrastructure = cls.create_infrastructure_services()
        cls.create_scenario()
        cls.create_places(infrastructure)
        cls.create_capacities()

    def test_number_of_places_in_base_scenario(self):
        """Test the number of places with capacity by year for a service"""
        self.suffix = '-number-of-locations'

        # in the base scenario there should be 2 places in area1
        # and 1 with capacity in area2 for service1
        self.count_capacities([2, 1, 0], service=self.service1)

        # only 1 in scenario, because capacity of place2 is set to 0
        self.count_capacities([1, 1, 0], service=self.service1,
                               scenario=self.scenario)
        # ..until 2021
        self.count_capacities([2, 1, 0], service=self.service1,
                               scenario=self.scenario, year=2022)

        # in the base scenario there should be 1 place in area1 for service2
        self.count_capacities([1, 0, 0], service=self.service2)
        self.count_capacities([2, 0, 0], service=self.service2, year=2030)
        self.count_capacities([2, 0, 0], service=self.service2, year=2035)
        self.count_capacities([1, 0, 0], service=self.service2,
                               scenario=self.scenario)
        self.count_capacities([1, 0, 0], service=self.service2,
                               scenario=self.scenario, year=2030)
        self.count_capacities([2, 0, 0], service=self.service2,
                               scenario=self.scenario, year=2033)
        self.count_capacities([1, 0, 0], service=self.service2,
                               scenario=self.scenario, year=2035)

        # in 2025-2029 there should be 2 places in area2
        self.count_capacities([2, 1, 0], service=self.service1, year=2024)

        self.count_capacities([2, 2, 0], service=self.service1, year=2025)
        self.count_capacities([2, 2, 0], service=self.service1, year=2029)

        self.count_capacities([2, 1, 0], service=self.service1, year=2030)
        self.count_capacities([2, 1, 0], service=self.service1, year=2035)

        # both services
        self.count_capacities([2, 1, 0], service=[self.service1, self.service2])


    def test_total_capacity(self):
        """Test the number of places with capacity by year for a service"""
        self.suffix = '-capacity'

        # service2 has no capacity in place2, should return 0, not None
        self.count_capacities([2, 0, 0], service=self.service2)
        # in the base scenario there should be 2 places in area1
        # and 1 with capacity in area2 for service1
        self.count_capacities([5, 44, 0], service=self.service1)
        # both services
        self.count_capacities([7, 44, 0], service=[self.service1, self.service2])

        # only 1 in scenario, because capacity of place2 is set to 0
        self.count_capacities([1, 44, 0], service=self.service1,
                               scenario=self.scenario)
        # ..until 2021
        self.count_capacities([34, 44, 0], service=self.service1,
                               scenario=self.scenario, year=2022)

    def count_capacities(self,
                       expected_values: List[int],
                       service: int = None,
                       year: int = None,
                       scenario: int = None):
        query_params = {'area_level': self.area1.area_level.pk, }
        if service is not None:
            if isinstance(service, list):
                query_params['service'] = [s.id for s in service]
            else:
                query_params['service'] = service.id
        if year is not None:
            query_params['year'] = year
        if scenario is not None:
            query_params['scenario'] = scenario.id

        response = self.post(self.url_key+self.suffix, data=query_params)
        # assert that the result is ordered by label
        actual = sorted(response.data, key=lambda f: f['label'])
        expected = [{'label': 'area1', 'value': expected_values[0], },
                    {'label': 'area2', 'value': expected_values[1], },
                    {'label': 'area3', 'value': expected_values[2], },
                                        ]
        self.assert_response_equals_expected(actual, expected)
