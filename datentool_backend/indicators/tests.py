from typing import List

import mapbox_vector_tile
from django.urls import reverse
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

from .models import (IndicatorType, Indicator, IndicatorTypeField,)
from .compute import (NumberOfLocations,
                      TotalCapacityInArea,
                      register_indicator_class,
                      ComputeIndicator)

from datentool_backend.infrastructure.models import FieldTypes
from datentool_backend.area.factories import AreaLevelFactory, AreaFactory
from datentool_backend.user.factories import (InfrastructureFactory,
                                              ServiceFactory,
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
        register_indicator_class()(DummyIndicator)
        IndicatorType._update_indicators_types()

    @classmethod
    def tearDownClass(cls):
        # unregister the dummy class
        del IndicatorType._indicator_classes[DummyIndicator.__name__]
        super().tearDownClass()

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
        indicator = NumberOfLocations(query_params={})
        str(indicator)

        indicator_types = IndicatorType.objects.all()

        # add an unknown indicator
        unknown_indicator = IndicatorFactory(indicator_type__classname='Unknown')
        self.assertQuerysetEqual(indicator_types.values_list('classname', flat=True),
                                 ['Unknown',
                                  DummyIndicator.__name__,
                                  NumberOfLocations.__name__,
                                  TotalCapacityInArea.__name__,
                                  ], ordered=False)
         # delete an indicator_type
        IndicatorType.objects.get(classname=NumberOfLocations.__name__).delete()

        #  change parameters of other indicators
        dummy_indicator = IndicatorType.objects.get(classname=DummyIndicator.__name__)
        dummy_fields = IndicatorTypeField.objects.filter(
            indicator_type__classname=DummyIndicator.__name__)
        self.assertEquals(len(dummy_fields), 2)

        dummy_indicator.name = 'NewName'
        dummy_indicator.save()
        dummy_fields[0].delete()
        self.assertEqual(dummy_fields[1].field_type.field_type,
                         DummyIndicator.parameters[dummy_fields[1].field_type.name])

        # change fieldtype
        f1 = dummy_fields[1]
        f1.field_type.field_type = FieldTypes.CLASSIFICATION
        f1.field_type.save()

        # add fields
        IndicatorTypeField.objects.create(indicator_type=dummy_indicator,
                                           field_type=f1.field_type,
                                           label='F1')
        IndicatorTypeField.objects.create(indicator_type=dummy_indicator,
                                           field_type=f1.field_type,
                                           label='F2')

        self.assertQuerysetEqual(indicator_types.values_list('classname', flat=True),
                                 ['Unknown',
                                  DummyIndicator.__name__,
                                  TotalCapacityInArea.__name__,
                                  ], ordered=False)

        # reset the indicators
        IndicatorType._update_indicators_types()
        self.assertQuerysetEqual(indicator_types.values_list('classname', flat=True),
                                 [NumberOfLocations.__name__,
                                  TotalCapacityInArea.__name__,
                                  DummyIndicator.__name__,
                                  ], ordered=False)

        dummy_indicator = IndicatorType.objects.get(classname=DummyIndicator.__name__)
        dummy_fields = IndicatorTypeField.objects.filter(
            indicator_type__classname=DummyIndicator.__name__)
        self.assertEquals(len(dummy_fields), 2)
        self.assertEquals(dummy_indicator.name, DummyIndicator.label)


class DummyIndicator(ComputeIndicator):
    label = 'TE'
    description = 'Random Indicator'
    parameters = {'Max_Value': FieldTypes.NUMBER, 'TextField': FieldTypes.STRING, }

    def compute(self):
        """"""

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


class TestIndicatorTypeAPI(TestAPIMixin, BasicModelReadTest, APITestCase):
    """Test to get an area indicator"""
    url_key = "indicatortypes"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        register_indicator_class()(DummyIndicator)
        IndicatorType._update_indicators_types()
        cls.obj = IndicatorType.objects.get(classname=DummyIndicator.__name__)

    @classmethod
    def tearDownClass(cls):
        # unregister the dummy class
        del IndicatorType._indicator_classes[DummyIndicator.__name__]
        super().tearDownClass()


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

        cls.obj = area_level = AreaLevelFactory(label_field='gen')
        cls.url_pk = cls.obj.pk
        coords = ((0, 0), (0, 10), (10, 10), (10, 0), (0, 0))
        coords = [(x + 1000000, y + 6500000) for x, y in coords]
        cls.area1 = AreaFactory(
            area_level=area_level,
            geom=MultiPolygon(Polygon(coords),
                              srid=3857),
            attributes={'gen': 'area1', },
        )
        coords = ((10, 10), (10, 20), (20, 20), (20, 10), (10, 10))
        coords = [(x + 1000000, y + 6500000) for x, y in coords]
        cls.area2 = AreaFactory(
            area_level=area_level,
            geom=MultiPolygon(Polygon(coords),
                              srid=3857),
            attributes={'gen': 'area2', },
        )
        cls.scenario = ScenarioFactory(planning_process__owner=cls.profile)

        infrastructure = InfrastructureFactory()
        cls.service1 = ServiceFactory(infrastructure=infrastructure)
        cls.service2 = ServiceFactory(infrastructure=infrastructure)

        # Places 1 and 2 are in Area1
        cls.place1 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000005, y=6500005))
        cls.place2 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000005, y=6500006))
        # Places 3 and 4 are in Area2
        cls.place3 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000015, y=6500015))
        cls.place4 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000015, y=6500015))
        # Place 5 is in no area
        cls.place5 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000025, y=6500025))

        CapacityFactory(place=cls.place1, service=cls.service1, capacity=1)
        CapacityFactory(place=cls.place1, service=cls.service2, capacity=2)
        CapacityFactory(place=cls.place2, service=cls.service1, capacity=4)
        # in the scenario, place2 should have no capacity in the base year for service1
        CapacityFactory(place=cls.place2, service=cls.service1,
                        scenario=cls.scenario, capacity=0)
        # but after 2022 it has capacity
        CapacityFactory(place=cls.place2, service=cls.service1,
                        scenario=cls.scenario, capacity=33, from_year=2022)

        # place 2 has only capacity from 2030 for service2
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2030, capacity=8)

        # in the scenario, place2 should have no capacity from year 2035 for service2
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2033, scenario=cls.scenario, capacity=16)
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2035, scenario=cls.scenario, capacity=0)

        # place 3 and 4 have capacity defined for service 1, but place 4 with capacity=0
        CapacityFactory(place=cls.place3, service=cls.service1, capacity=44)
        CapacityFactory(place=cls.place4, service=cls.service1, capacity=0)

        # but between 2025 and 2030 there is capacity in place 4
        CapacityFactory(place=cls.place4, service=cls.service1,
                        from_year=2025, capacity=100)
        CapacityFactory(place=cls.place4, service=cls.service1,
                        from_year=2030, capacity=0)

        # place 5 has capacity defined, but is in no Area
        CapacityFactory(place=cls.place5, service=cls.service1, capacity=66)
        CapacityFactory(place=cls.place5, service=cls.service2, capacity=77)


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

    def test_total_capacity(self):
        """Test the number of places with capacity by year for a service"""
        self.indicator = IndicatorFactory(
            indicator_type__classname=TotalCapacityInArea.__name__)

        # in the base scenario there should be 2 places in area1
        # and 1 with capacity in area2 for service1
        self.count_capacitites([5, 44], service=self.service1)

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
        response = self.get(url, data={'indicator': self.indicator.pk, })
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

