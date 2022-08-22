import pandas as pd

from django.test import TestCase
from test_plus import APITestCase

from django.urls import reverse
from datentool_backend.api_test import LoginTestCase


from datentool_backend.indicators.factories import (
    RouterFactory,
    MatrixCellPlaceFactory,
    MatrixCellStopFactory,
    MatrixPlaceStopFactory,
    MatrixStopStopFactory)

from datentool_backend.infrastructure.factories import ServiceFactory, Service


class TestIndicator(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_router(self):
        RouterFactory()

    def test_matrix_cell_place(self):
        MatrixCellPlaceFactory()

    def test_matrix_cell_stop(self):
        MatrixCellStopFactory()

    def test_matrix_place_stop(self):
        MatrixPlaceStopFactory()

    def test_matrix_stop_stop(self):
        MatrixStopStopFactory()


class TestIndicatorDescription(LoginTestCase,
                               APITestCase,
                               ):
    """Test the indicator descriptions"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service_school = ServiceFactory(
            name='Grundschule',
            quota_type='Wird Quota Type verwendet???',
            capacity_singular_unit='Grundschulplatz',
            capacity_plural_unit='Grundschulplätze',
            has_capacity=True,
            demand_singular_unit='Grundschüler:in',
            demand_plural_unit='Grundschüler:innen',
            demand_name='Grundschulbesuch',
            demand_description='Grundschulbesuche Klassen 1-4',
            facility_singular_unit='Schule',
            facility_article='die',
            facility_plural_unit='Schulen',
            direction_way_relationship=Service.WayRelationship.TO,
            demand_type=Service.DemandType.QUOTA,
        )

        cls.infra = cls.service_school.infrastructure

        cls.service_doctor = ServiceFactory(
            infrastructure=cls.infra,
            name='Hausarzt',
            quota_type='Wird Quota Type verwendet???',
            capacity_singular_unit='Praxis',
            capacity_plural_unit='Praxen',
            has_capacity=False,
            demand_singular_unit='Arztkontakt',
            demand_plural_unit='Arztkontakte',
            demand_name='Hausarztbesuche',
            demand_description='Besuche pro Jahr',
            facility_singular_unit='Praxis',
            facility_article='die',
            facility_plural_unit='Praxen',
            direction_way_relationship=Service.WayRelationship.TO,
            demand_type=Service.DemandType.FREQUENCY,
        )

        cls.service_fire = ServiceFactory(
            infrastructure=cls.infra,
            name='Feuerwehr',
            quota_type='Wird Quota Type verwendet???',
            capacity_singular_unit='Löschzug',
            capacity_plural_unit='Löschzüge',
            has_capacity=False,
            demand_singular_unit='Brand',
            demand_plural_unit='Brände',
            demand_name='Brandeinsatz',
            demand_description='Brandeinsätze pro Jahr',
            facility_singular_unit='Gerätehaus',
            facility_article='das',
            facility_plural_unit='Gerätehäuser',
            direction_way_relationship=Service.WayRelationship.FROM,
            demand_type=Service.DemandType.UNIFORM,
        )

        cls.services = [cls.service_school, cls.service_doctor, cls.service_fire]

    def test_service_indicators(self):
        """Test the description of the fixed indicators"""
        self.client.force_login(self.profile.user)

        for service in self.services:
            url = reverse('services-get-indicators', kwargs={'pk': service.pk})
            response = self.get(url)
            self.assert_http_200_ok(response)
            result = pd.DataFrame(response.data).set_index('name')
            print(result['title'])
            print(result['description'])
            print(result['result_type'])
            print(result['additional_parameters'])

    def test_fixed_indicators(self):
        """Test the description of the fixed indicators"""
        self.client.force_login(self.profile.user)

        base_url = 'fixedindicators'
        indicators = ['capacity',
                      'demand',
                      'number-of-locations',
                      'aggregate-population',
                      'population-details',
                      'reachability-place',
                      'reachibility-cell',
                      ]

        for indicator in indicators:
            url = reverse(f'{base_url}-{indicator}')
            response = self.get(url)
            self.assert_http_200_ok(response)
            result = response.data
            print(result['title'])
            print(result['description'])
            print(result['result_type'])
            print(result['additional_parameters'])