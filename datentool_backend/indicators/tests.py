from typing import List

from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Point, Polygon, MultiPolygon

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        BasicModelReadTest,
                                        )
from datentool_backend.area.tests import TestAPIMixin, TestPermissionsMixin


from .factories import (RouterFactory, IndicatorFactory, MatrixCellPlaceFactory,
                        MatrixCellStopFactory, MatrixPlaceStopFactory,
                        MatrixStopStopFactory)

from .factories import (RouterFactory,
                        IndicatorFactory,
                        )

from .models import (IndicatorType, Indicator)
from .compute import NumberOfLocations

from datentool_backend.area.factories import AreaLevelFactory, AreaFactory
from datentool_backend.user.factories import (InfrastructureFactory,
                                              ServiceFactory,
                                              YearFactory,
                                              PlanningProcess)
from datentool_backend.infrastructure.factories import (ScenarioFactory,
                                                        PlaceFactory,
                                                        ServiceFactory,
                                                        CapacityFactory)

from faker import Faker
faker = Faker('de-DE')


class TestIndicator(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        IndicatorType._check_indicators()

    def test_router(self):
        router = RouterFactory()

    def test_indicator(self):
        num_locs = IndicatorType.objects.get(
            classname=NumberOfLocations.__name__)
        indicator = IndicatorFactory(indicator_type=num_locs)

    def test_matrix_cell_place(self):
        matrix_cell_place = MatrixCellPlaceFactory()

    def test_matrix_cell_stop(self):
        matrix_cell_stop = MatrixCellStopFactory()

    def test_matrix_place_stop(self):
        matrix_place_stop = MatrixPlaceStopFactory()

    def test_matrix_stop_stop(self):
        matrix_stop_stop = MatrixStopStopFactory()

    def test_indicator_types(self):
        """test if the indicator types are registred"""
        print(NumberOfLocations)



class TestRouterAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "routers"
    factory = RouterFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(name = faker.word(),
                    osm_file = faker.file_path(),
                    tiff_file = faker.file_path(),
                    gtfs_file = faker.file_path(),
                    build_date = faker.date(),
                    buffer = faker.random_number(digits=2))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestIndicatorAPI(WriteOnlyWithCanEditBaseDataTest,
                       TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "indicators"
    factory = IndicatorFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        indicator: Indicator = cls.obj
        service = indicator.service.pk
        indicator_type = indicator.indicator_type.pk

        data = dict(indicator_type=indicator_type,
                    name=faker.word(),
                    parameters=faker.json(),
                    service=service)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestAreaIndicatorAPI(TestAPIMixin, BasicModelReadTest, APITestCase):
    """Test to get an area indicator"""
    url_key = "areaindicators"

    @property
    def query_params(self):
        return {'indicator': self.indicator.pk,
                'area_level': self.area1.area_level.pk, }

    @classmethod
    def tearDownClass(cls):
        PlanningProcess.objects.all().delete()
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.indicator = IndicatorFactory(
            indicator_type__classname=NumberOfLocations.__name__)

        cls.obj = area_level = AreaLevelFactory()
        cls.url_pk = cls.obj.pk
        cls.area1 = AreaFactory(
            area_level=area_level,
            geom=MultiPolygon(Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0))),
                              srid=3857),
            attributes={'name': 'area1',},
            )
        cls.area2 = AreaFactory(
            area_level=area_level,
            geom=MultiPolygon(Polygon(((10, 10), (10, 20), (20, 20), (20, 10), (10, 10))),
                              srid=3857),
            attributes={'name': 'area2',},
            )
        cls.scenario = ScenarioFactory(planning_process__owner=cls.profile)

        infrastructure = InfrastructureFactory()
        cls.service1 = ServiceFactory(infrastructure=infrastructure)
        cls.service2 = ServiceFactory(infrastructure=infrastructure)

        # Places 1 and 2 are in Area1
        cls.place1 = PlaceFactory(infrastructure=infrastructure, geom=Point(x=5, y=5))
        cls.place2 = PlaceFactory(infrastructure=infrastructure, geom=Point(x=5, y=6))
        # Places 3 and 4 are in Area2
        cls.place3 = PlaceFactory(infrastructure=infrastructure, geom=Point(x=15, y=15))
        cls.place4 = PlaceFactory(infrastructure=infrastructure, geom=Point(x=15, y=15))
        # Place 5 is in no area
        cls.place5 = PlaceFactory(infrastructure=infrastructure, geom=Point(x=25, y=25))

        CapacityFactory(place=cls.place1, service=cls.service1)
        CapacityFactory(place=cls.place1, service=cls.service2)
        CapacityFactory(place=cls.place2, service=cls.service1)
        # in the scenario, place2 should have no capacity in the base year for service1
        CapacityFactory(place=cls.place2, service=cls.service1,
                        scenario=cls.scenario, capacity=0)
        # but after 2022 it has capacity
        CapacityFactory(place=cls.place2, service=cls.service1,
                        scenario=cls.scenario, capacity=33, from_year=2022)

        # place 2 has only capacity from 2030 for service2
        CapacityFactory(place=cls.place2, service=cls.service2, from_year=2030)

        # in the scenario, place2 should have no capacity from year 2035 for service2
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2033, scenario=cls.scenario)
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2035, scenario=cls.scenario, capacity=0)

        # place 3 and 4 have capacity defined for service 1, but place 4 with capacity=0
        CapacityFactory(place=cls.place3, service=cls.service1)
        CapacityFactory(place=cls.place4, service=cls.service1, capacity=0)

        # but between 2025 and 2030 there is capacity in place 4
        CapacityFactory(place=cls.place4, service=cls.service1,
                        from_year=2025, capacity=100)
        CapacityFactory(place=cls.place4, service=cls.service1,
                        from_year=2030, capacity=0)

        # place 5 has capacity defined, but is in no Area
        CapacityFactory(place=cls.place5, service=cls.service1)
        CapacityFactory(place=cls.place5, service=cls.service2)


    def test_numer_of_places_in_base_scenario(self):
        """Test the number of places with capacity by year for a service"""

        # only 1 in scenario, because capacity of place2 is set to 0
        self.count_capacitites([1, 1], service=self.service1, scenario=self.scenario)

        # in the base scenario there should be 2 places in area1
        # and 1 with capacity in area2 for service1
        self.count_capacitites([2, 1], service=self.service1)

        self.count_capacitites([2, 1], service=self.service1, scenario=self.scenario, year=2022)

        # in the base scenario there should be 1 place in area1 for service2
        self.count_capacitites([1, 0], service=self.service2)
        self.count_capacitites([2, 0], service=self.service2, year=2030)
        self.count_capacitites([2, 0], service=self.service2, year=2035)
        self.count_capacitites([1, 0], service=self.service2, scenario=self.scenario)
        self.count_capacitites([1, 0], service=self.service2, scenario=self.scenario, year=2030)
        self.count_capacitites([2, 0], service=self.service2, scenario=self.scenario, year=2033)
        self.count_capacitites([1, 0], service=self.service2, scenario=self.scenario, year=2035)

        # in 2025-2029 there should be 2 places in area2
        self.count_capacitites([2, 1], service=self.service1, year=2024)

        self.count_capacitites([2, 2], service=self.service1, year=2025)
        self.count_capacitites([2, 2], service=self.service1, year=2029)

        self.count_capacitites([2, 1], service=self.service1, year=2030)
        self.count_capacitites([2, 1], service=self.service1, year=2035)

    def count_capacitites(self,
                       expected_values: List[int],
                       service: int=None,
                       year: int=None,
                       scenario: int=None):
        query_params = {'indicator': self.indicator.pk,
                        'area_level': self.area1.pk,}
        if service is not None:
            query_params['service'] = service.id
        if year is not None:
            query_params['year'] = year
        if scenario is not None:
            query_params['scenario'] = scenario.id

        response = self.get_check_200(self.url_key+'-list', data=query_params)
        expected = [{'name': 'area1', 'value': expected_values[0],},
                    {'name': 'area2', 'value': expected_values[1],}]
        self.assert_response_equals_expected(response.data, expected)

