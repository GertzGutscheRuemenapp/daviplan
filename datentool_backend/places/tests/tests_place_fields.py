import logging
logger = logging.getLogger(name='test')

from typing import Tuple, Set, List
import json

import pandas as pd

from django.test import TestCase
from django.contrib.gis.geos import Point
from test_plus import APITestCase

from datentool_backend.api_test import (BasicModelTest, DemoModeReadOnlyTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        )
from datentool_backend.api_test import TestAPIMixin, TestPermissionsMixin

from datentool_backend.user.factories import ProfileFactory
from datentool_backend.places.factories import ScenarioFactory, Scenario
from datentool_backend.user.models import Profile
from datentool_backend.infrastructure.models import (
    Infrastructure,
    InfrastructureAccess,
    Service)

from datentool_backend.infrastructure.factories import (InfrastructureFactory,
                                                        ServiceFactory)
from datentool_backend.places.factories import (PlaceFactory,
                                                CapacityFactory,
                                                PlaceFieldFactory)
from datentool_backend.places.models import (
    Place,
    FieldTypes,
    PlaceField,
    PlaceAttribute,
)
from datentool_backend.area.factories import FClassFactory, FieldTypeFactory

from faker import Faker
faker = Faker('de-DE')


class TestCapacity(TestCase):

    def test_capacity(self):
        """"""
        infrastructure = InfrastructureFactory()
        capacity = CapacityFactory(place__infrastructure=infrastructure,
                                   service__infrastructure=infrastructure)
        logger.debug(capacity)
        logger.debug(capacity.place)

    def test_fclass(self):
        """"""
        fclass = FClassFactory()
        logger.debug(fclass)

    def test_place_field(self):
        """"""
        place_field = PlaceFieldFactory()
        logger.debug(place_field)


class TestPlaceAPI(WriteOnlyWithCanEditBaseDataTest, DemoModeReadOnlyTest,
                   TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "places"
    capacity_url = "capacities"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = place = PlaceFactory()

        infrastructure = place.infrastructure.pk

        ft_age = FieldTypeFactory(ftype=FieldTypes.NUMBER)
        field1 = PlaceFieldFactory(
            name='age',
            infrastructure=place.infrastructure,
            field_type=ft_age,
            sensitive=False,
        )

        ft_name = FieldTypeFactory(ftype=FieldTypes.STRING)
        field2 = PlaceFieldFactory(
            name='surname',
            infrastructure=place.infrastructure,
            field_type=ft_name,
            sensitive=False,
            is_label=True,
        )

        place.attributes={'age': faker.pyint(), 'surname': faker.name()}
        place.save()

        geom = place.geom.ewkt
        attributes={'age': faker.pyint(), 'surname': faker.name()}

        geojson = {
            'geom': geom,
            'name': faker.word(),
            'infrastructure': infrastructure,
            'attributes': attributes,
        }

        cls.post_data = geojson
        geojson_put = geojson.copy()
        geojson_put['id'] = place.id
        cls.put_data = geojson_put

        geojson_patch = geojson_put.copy()
        pnt = Point(x=10, y=50, srid=4326)
        geojson_patch['geom'] = pnt.ewkt

        expected_patched = {'geom': pnt.transform(3857, clone=True).ewkt}

        cls.patch_data = geojson_patch
        cls.expected_patch_data = expected_patched

    def test_sensitive_data(self):
        """Test if sensitive data is correctly shown"""
        pr1 = ProfileFactory(admin_access=False)
        pr2 = ProfileFactory(admin_access=False)
        place: Place = self.obj

        infr: Infrastructure = place.infrastructure
        self.assertEqual(infr.label_field, 'surname')

        infr.accessible_by.set([pr1, pr2])
        infr.save()

        i1 = InfrastructureAccess.objects.get(infrastructure=infr, profile=pr1)
        i1.allow_sensitive_data = False
        i1.save()

        i2 = InfrastructureAccess.objects.get(infrastructure=infr, profile=pr2)
        i2.allow_sensitive_data = True
        i2.save()

        field_type = FieldTypeFactory(ftype=FieldTypes.NUMBER)
        field1 = PlaceFieldFactory(name='harmless', sensitive=False,
                                   field_type=field_type,
                                   infrastructure=infr)
        field2 = PlaceFieldFactory(name='very_secret', sensitive=True,
                                   field_type=field_type,
                                   infrastructure=infr)

        #  test the label
        label = place.attributes.get(field__is_label=True).value
        self.assertEqual(place.label, label)

        attributes = {'harmless': 123, 'very_secret': 456, }
        place.attributes = attributes
        place.save()

        # user1 should not see the secret attributes
        self.client.logout()
        self.client.force_login(pr1.user)
        response = self.get(self.url_key + '-detail', **self.kwargs)
        attrs = response.data['attributes']
        self.assertDictEqual(attrs, {'harmless': 123})

        # user1 should see the secret attributes
        self.client.logout()
        self.client.force_login(pr2.user)
        response = self.get(self.url_key + '-detail', **self.kwargs)
        attrs = response.data['attributes']
        self.assertDictEqual(attrs, attributes)

        # with admin access, also user1 should see the secret attributes
        self.client.logout()
        pr1.admin_access = True
        pr1.save()
        self.client.force_login(pr1.user)
        response = self.get(self.url_key + '-detail', **self.kwargs)
        attrs = response.data['attributes']
        self.assertDictEqual(attrs, attributes)

        self.client.logout()
        self.client.force_login(self.profile.user)

    def setup_place(self) -> Tuple[Profile, Place]:
        pr1 = ProfileFactory(can_edit_basedata=True)
        place: Place = self.obj

        infr: Infrastructure = place.infrastructure
        infr.accessible_by.set([pr1])
        infr.save()

        field1 = PlaceFieldFactory(name='intfield', sensitive=False,
                                   field_type__ftype=FieldTypes.NUMBER,
                                   infrastructure=infr)
        field2 = PlaceFieldFactory(name='textfield', sensitive=False,
                                   field_type__ftype=FieldTypes.STRING,
                                   infrastructure=infr)
        field3 = PlaceFieldFactory(
            name='classfield',
            sensitive=False,
            field_type__ftype=FieldTypes.CLASSIFICATION,
            infrastructure=infr)

        fclass1 = FClassFactory(ftype=field3.field_type,
                                order=1,
                                value='Category_1')
        fclass2 = FClassFactory(ftype=field3.field_type,
                                order=2,
                                value='Category_2')

        attributes = {'intfield': 123,
                      'textfield': 'ABC',
                      'classfield': 'Category_1', }
        place.attributes = attributes
        place.save()

        return pr1, place

    def test_update_attributes(self):
        """Test update of attributes"""
        pr1, place = self.setup_place()

        patch_data = {'name': 'NewName',
                      'attributes': {'intfield': 456,
                                     'textfield': 'DEF',
                                     'classfield': 'Category_2', }
                      }

        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_403(msg=response.content)

        self.client.logout()
        self.client.force_login(pr1.user)

        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        # check the results returned by the view
        attrs = response.data['attributes']
        self.compare_data(attrs, patch_data)

        # check if the changed data is really in the database
        response = self.get_check_200(self.url_key + '-detail', pk=place.pk)
        attrs = response.data['attributes']
        self.compare_data(attrs, patch_data)

        # patch only one value
        patch_data = {'attributes': {'intfield': 678, }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        expected = {'attributes': {'intfield': 678,
                                   'textfield': 'DEF',
                                   'classfield': 'Category_2', }
                    }
        # check the results returned by the view
        attrs = response.data['attributes']
        self.compare_data(attrs, expected)

        # check if the changed data is really in the database
        response = self.get_check_200(self.url_key + '-detail', pk=place.pk)
        attrs = response.data['attributes']
        self.compare_data(attrs, expected)

        # check if invalid attributes return a BadRequest
        patch_data = {'attributes': {'integerfield': 456, }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'intfield': '456', }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'textfield': 12.3, }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'classfield': 'Category_7', }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        # this should work
        patch_data = {'attributes': {'classfield': 'Category_1', }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        expected = {'attributes': {'intfield': 678,
                                   'textfield': 'DEF',
                                   'classfield': 'Category_1', }
                    }

        attrs = response.data['attributes']
        self.compare_data(attrs, patch_data)

    def test_delete_placefield(self):
        """
        Test, if the deletion of a PlaceField
        and a FClass cascades to the Place Attributes
        """
        profile, place1 = self.setup_place()
        self.client.logout()
        self.client.force_login(profile.user)

        attributes2 = {'intfield': 789,
                       'classfield': 'Category_2', }
        place2 = PlaceFactory(infrastructure=place1.infrastructure,
                              attributes=attributes2)

        place_fields = PlaceField.objects.filter(
            infrastructure=place1.infrastructure,
            name__in=['intfield', 'textfield', 'classfield'])

        for place_field in place_fields:
            # deleting the place field should fail,
            # if there are attributes of this place_field
            response = self.delete('placefields-detail', pk=place_field.pk,
                                   extra={'format': 'json'})
            self.response_403(msg=response.content)

        field_name = 'intfield'
        int_field = PlaceField.objects.get(name=field_name,
                                           infrastructure=place1.infrastructure)

        # deleting the place field should cascadedly delete the attribute
        # from the place attributes
        response = self.delete('placefields-detail',
                               pk=int_field.pk,
                               data=dict(force=True), extra={'format': 'json'})
        self.response_204(msg=response.content)

        place_attributes = PlaceAttribute.objects.filter(
            place__infrastructure=place1.infrastructure, field__name=field_name)
        self.assertQuerysetEqual(
            place_attributes, [], msg=f'{field_name} should be removed from the place attributes')

        field_name = 'textfield'
        text_field = PlaceField.objects.get(name=field_name,
                                            infrastructure=place1.infrastructure)
        # remove the text_field from place1, so there is no text_field defined
        attributes = {'classfield': 'Category_1', }
        place1.attributes = attributes
        place1.save()

        # it should delete the text_field even without force,
        # because it is not referenced any more
        response = self.delete('placefields-detail',
                               pk=text_field.pk,
                               data=dict(force=False), extra={'format': 'json'})
        self.response_204(msg=response.content)

    def test_get_capacity_for_service(self):
        """get filtered queryset for service"""
        place1: Place = self.obj
        place2 = PlaceFactory(infrastructure=place1.infrastructure)
        service1 = ServiceFactory(infrastructure=place1.infrastructure)
        service2 = ServiceFactory(infrastructure=place1.infrastructure)
        service3 = ServiceFactory(infrastructure=place1.infrastructure)

        place1.service_capacity.set([service1, service2])
        place2.service_capacity.set([service3, service2],
                                    through_defaults=dict(capacity=0))

        # default capacity has from_year=0 and capacity=0
        # add two more capacities
        CapacityFactory(service=service3, place=place2,
                        from_year=2023, capacity=123)
        CapacityFactory(service=service3, place=place2,
                        from_year=2021, capacity=55)

        # test if the correct places which offer a service are returned
        self.check_place_with_capacity(service1, expected_place_ids={place1.id})
        self.check_place_with_capacity(service2, expected_place_ids={place1.id, place2.id})
        self.check_place_with_capacity(service3, expected_place_ids={place2.id})

        year_expected = {2020: 0,
                         2021: 55,
                         2022: 55,
                         2023: 123,
                         2024: 123,
                         }

        # test if the correct capacity is returned for different years
        for year, expected in year_expected.items():
            response = self.get(self.capacity_url + '-list',
                                data=dict(place=place2.id, service=service3.id,
                                          year=year))
            self.assertEqual(len(response.data), 1)
            capacity = response.data[0]['capacity']
            self.assertEqual(capacity, expected)

        # this should fail, because there is no service3 offered at place1
        response = self.get(self.capacity_url + '-list',
                            data=dict(place=place1.id, service=service3.id,
                                      year=2024))
        self.assertEqual(len(response.data), 0)

    def check_place_with_capacity(self, service: Service,
                                  place: int = None,
                                  scenario: int = None,
                                  year: int = None,
                                  expected_place_ids: Set[int] = None,
                                  expected: List[int] = None,
                                  expect_forbidden: bool = False):
        data = dict(service=service.id)
        if scenario is not None:
            data['scenario'] = scenario
        if year is not None:
            data['year'] = year
        if place is not None:
            data['place'] = place
        response = self.get(self.capacity_url + '-list',
                            data=data)

        if expect_forbidden:
            self.response_403(msg=response.content)
            return

        self.response_200(msg=response.content)
        if expected_place_ids is not None:
            self.assertSetEqual({d['place'] for d in response.data},
                                expected_place_ids)
        assert all((d['service'] == service.id for d in response.data))
        if expected is not None:
            self.assertListEqual(
                [d['capacity'] for d in response.data], expected)

    def create_testusers(self, scenario: Scenario, infrastructure: Infrastructure):
        """Create testusers with no access to service or planning process"""
        self.profile2 = ProfileFactory(admin_access=False,
                                      can_edit_basedata=False,
                                      can_create_process=False)
        self.profile3 = ProfileFactory(admin_access=False,
                                      can_edit_basedata=False,
                                      can_create_process=False)
        self.profile4 = ProfileFactory(admin_access=False,
                                      can_edit_basedata=False,
                                      can_create_process=False)
        self.profile5 = ProfileFactory(admin_access=False,
                                      can_edit_basedata=False,
                                      can_create_process=False)

        infrastructure.accessible_by.add(self.profile3)
        infrastructure.accessible_by.add(self.profile4)
        planning_process = scenario.planning_process
        planning_process.users.add(self.profile4)
        planning_process.users.add(self.profile5)

    def test_check_capacity_for_scenario(self):
        scenario1 = ScenarioFactory()
        planning_process = scenario1.planning_process
        planning_process.users.add(self.profile)
        scenario2 = ScenarioFactory(planning_process=planning_process)
        scenario3 = ScenarioFactory(planning_process=planning_process)

        place1: Place = self.obj
        place2 = PlaceFactory(infrastructure=place1.infrastructure)
        service1 = ServiceFactory(infrastructure=place1.infrastructure)
        service2 = ServiceFactory(infrastructure=place1.infrastructure)

        CapacityFactory(place=place1, service=service2, capacity=99)
        CapacityFactory(place=place1, service=service1,
                        from_year=2025, capacity=77)
        CapacityFactory(place=place1, service=service1, capacity=50)
        CapacityFactory(place=place1, service=service1,
                        capacity=100, scenario=scenario1)
        CapacityFactory(place=place1, service=service1,
                        capacity=100,
                        scenario=scenario3)
        CapacityFactory(place=place1, service=service1,
                        from_year=2022, capacity=200,
                        scenario=scenario3)
        CapacityFactory(place=place1, service=service1,
                        from_year=2030, capacity=0,
                        scenario=scenario3)

        #  In the base scenario, test the scenario for service1 and service2
        self.check_place_with_capacity(service1, year=0, place=place1.id, expected=[50])
        self.check_place_with_capacity(service2, year=0, place=place1.id, expected=[99])

        #  In scenario1, it should change
        self.check_place_with_capacity(service1, year=0, scenario=scenario1.pk,
                                       place=place1.id, expected=[100])
        #  In scenario2, no new capacity defined,
        # so take the base value for the base year
        self.check_place_with_capacity(service1, year=0, scenario=scenario2.pk,
                                       place=place1.id, expected=[50])
        #  .. and the base-scenario value vor year 2026
        self.check_place_with_capacity(service1, scenario=scenario2.pk,
                                       year=2026, place=place1.id, expected=[77])
        #  In scenario3, it should change over time from 100 over 200 to 0
        self.check_place_with_capacity(service1,
                                       scenario=scenario3.pk, year=2021,
                                       place=place1.id, expected=[100])
        self.check_place_with_capacity(service1,
                                       scenario=scenario3.pk, year=2022,
                                       place=place1.id, expected=[200])
        self.check_place_with_capacity(service1,
                                       scenario=scenario3.pk, year=2025,
                                       place=place1.id, expected=[200])
        self.check_place_with_capacity(service1,
                                       scenario=scenario3.pk, year=2030,
                                       place=place1.id, expected=[0])


        CapacityFactory(place=place2, service=service1, capacity=88)
        CapacityFactory(place=place2, service=service1, from_year=2022, capacity=99)
        CapacityFactory(place=place2, service=service1, scenario=scenario1, capacity=55)
        CapacityFactory(place=place2, service=service1, scenario=scenario2, capacity=33)

        self.check_place_with_capacity(service1, year=0, expected=[50, 88])
        self.check_place_with_capacity(service1, year=2023, expected=[50, 99])
        self.check_place_with_capacity(service1, year=2026, expected=[77, 99])
        self.check_place_with_capacity(service1, year=0, scenario=scenario1.id, expected=[100, 55])
        self.check_place_with_capacity(service1, year=0, scenario=scenario2.id, expected=[50, 33])
        self.check_place_with_capacity(service1, year=0, scenario=scenario3.id, expected=[100, 88])

        """Test the number of places and the total capacity by scenario"""
        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service1.pk,
            year=2018,
            expected_values=[(2, 50 + 88), (2, 100 + 55),
                             (2, 50 + 33), (2, 100 + 88)])

        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service1.pk,
            year=2022,
            expected_values=[(2, 50 + 99), (2, 100 + 55),
                             (2, 50 + 33), (2, 200 + 99)])

        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service1.pk,
            year=2025,
            expected_values=[(2, 77 + 99), (2, 100 + 55),
                             (2, 77 + 33), (2, 200 + 99)])

        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service1.pk,
            year=2030,
            expected_values=[(2, 77 + 99), (2, 100 + 55),
                             (2, 77 + 33), (1, 99)])

        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service2.pk,
            year=2018,
            expected_values=[(1, 99), (1, 99), (1, 99), (1, 99)])

        self.check_total_nplaces_capacity(
            scenario=scenario2.pk,
            service=service1.pk,
            year=2030,
            expected_values=[(2, 77 + 33)])

        # test the permissions for other users
        self.create_testusers(scenario1, place1.infrastructure)


        # profile 3 is allowed to infrastructure but not to planning process
        self.client.force_login(self.profile3.user)
        self.check_place_with_capacity(service1,
                                       year=2023,
                                       scenario=scenario1.id,
                                       expect_forbidden=True)
        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service2.pk,
            scenario=scenario2.pk,
            year=2030,
            expect_forbidden=True)

        # profile 4 is allowed to infrastructure and to planning process
        self.client.force_login(self.profile4.user)
        self.check_place_with_capacity(service1,
                                       year=0,
                                       scenario=scenario1.id,
                                       expected=[100, 55]
                                       )
        self.check_total_nplaces_capacity(
            scenario=scenario2.pk,
            service=service1.pk,
            year=2030,
            expected_values=[(2, 77 + 33)])

        # profile 5 is not allowed to infrastructure but to planning process
        self.client.force_login(self.profile5.user)
        self.check_place_with_capacity(service1,
                                       year=2023,
                                       scenario=scenario1.id,
                                       expect_forbidden=True)
        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service2.pk,
            scenario=scenario2.pk,
            year=2030,
            expect_forbidden=True)

        # profile 2 is not allowed to infrastructure and not to planning process
        self.client.force_login(self.profile2.user)
        self.check_place_with_capacity(service1, year=2023, expect_forbidden=True)
        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service2.pk,
            year=2030,
            expect_forbidden=True)

        # profile 3 is allowed to infrastructure but not to planning process
        # but may see base scenario
        self.client.force_login(self.profile3.user)
        self.check_place_with_capacity(service1, year=2023, expected=[50, 99])

        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service2.pk,
            year=2018,
            expected_values=[(1, 99), (1, 99), (1, 99), (1, 99)])

        # profile 5 is not allowed to infrastructure but to planning process
        # is forbidden to see the indicator
        self.client.force_login(self.profile5.user)
        self.check_place_with_capacity(service1, year=2023, expect_forbidden=True)
        self.check_total_nplaces_capacity(
            planning_process=planning_process.pk,
            service=service2.pk,
            scenario=scenario2.pk,
            year=2030,
            expect_forbidden=True)

    def check_total_nplaces_capacity(self,
                                     service: int,
                                     year: int,
                                     expected_values: List[Tuple[int, float]] = [],
                                     planning_process: int = None,
                                     scenario: int = None,
                                     expect_forbidden: bool = False,
                                     ):
        params = {'year': year}
        if planning_process:
            params['planningprocess'] = planning_process
        if scenario:
            params['scenario'] = scenario
        response = self.get('services-total-capacity-in-year',
                            pk=service,
                            data=params)

        if expect_forbidden:
            self.response_403(msg=response.content)
            return

        self.response_200(msg=response.content)
        r1 = json.loads(response.content)
        expected = []
        if scenario:
            scenario_ids = [scenario]
        else:
            scenario_ids = [0] + list(Scenario.objects
                .filter(planning_process=planning_process)
                .values_list('id', flat=True))

        for i, scenario_id in enumerate(scenario_ids):
            expected_value = expected_values[i]
            expected.append({'scenarioId': scenario_id,
                             'nPlaces': expected_value[0],
                             'totalCapacity': expected_value[1], })
        self.assert_response_equals_expected(r1, expected)

    def test_replace_capacities(self):
        """Test replacing capacities with new values"""
        url = 'capacities-replace'
        scenario1 = ScenarioFactory()

        planning_process = scenario1.planning_process
        owner = planning_process.owner
        planning_process.allow_shared_change = False
        planning_process.save()

        place1: Place = self.obj
        service1 = ServiceFactory(infrastructure=place1.infrastructure)

        CapacityFactory(place=place1, service=service1, capacity=99)
        CapacityFactory(place=place1, service=service1,
                        from_year=2025, capacity=77)
        CapacityFactory(place=place1, service=service1,
                        from_year=2025, capacity=0)

        data = {'scenario': scenario1.pk,
                'place': place1.pk,
                'service': service1.pk,
                'capacities': [{'from_year': 2022, 'capacity': 33,},
                               {'from_year': 2030, 'capacity': 44,},
                               ],}

        res = self.post(url, data=data, extra={'format': 'json',})
        self.assert_http_403_forbidden(res)

        planning_process.users.add(self.profile)
        res = self.post(url, data=data, extra={'format': 'json',})
        self.assert_http_403_forbidden(res)

        planning_process.allow_shared_change = True
        planning_process.save()
        res = self.post(url, data=data, extra={'format': 'json',})
        self.assert_http_200_ok(res)

        expected = pd.Series(index=pd.Index([2022, 2030], name='from_year'),
                             data=[33., 44.],
                             name='capacity')

        actual = pd.DataFrame(res.data).set_index('from_year').capacity
        pd.testing.assert_series_equal(actual, expected)

        self.client.force_login(owner.user)
        planning_process.allow_shared_change = False
        planning_process.save()

        data['capacities'] = [{'from_year': 2022, 'capacity': 19,},
                               {'from_year': 2035, 'capacity': 49,},
                               ]
        res = self.post(url, data=data, extra={'format': 'json',})
        self.assert_http_200_ok(res)

        expected = pd.Series(index=pd.Index([2022, 2035], name='from_year'),
                             data=[19., 49.],
                             name='capacity')

        actual = pd.DataFrame(res.data).set_index('from_year').capacity
        pd.testing.assert_series_equal(actual, expected, check_like=True)


class TestCapacityAPI(WriteOnlyWithCanEditBaseDataTest, DemoModeReadOnlyTest,
                      TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "capacities"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        infrastructure = InfrastructureFactory()
        infrastructure.accessible_by.add(cls.profile)
        infrastructure.accessible_by.add(cls.demo_profile)
        capacity = CapacityFactory(place__infrastructure=infrastructure,
                                   service__infrastructure=infrastructure)

        cls.obj = capacity
        place = capacity.place.pk
        service = capacity.service.pk
        scenario = None

        data = dict(place=place,
                    service=service,
                    capacity=faker.pyfloat(positive=True),
                    from_year=faker.year(),
                    scenario=scenario)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

        cls.query_params = {'service': service, }


class TestFieldTypeNUMSTRAPI(WriteOnlyWithCanEditBaseDataTest, DemoModeReadOnlyTest,
                             TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fieldtypes"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = FieldTypeFactory(ftype=FieldTypes.NUMBER)
        data = dict(ftype=FieldTypes.NUMBER,
                    name=faker.word(),
                    )
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestFieldTypeCLAAPI(WriteOnlyWithCanEditBaseDataTest, DemoModeReadOnlyTest,
                          TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fieldtypes"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = FieldTypeFactory(ftype=FieldTypes.CLASSIFICATION)

        fclass_set = [{'order': 1, 'value': faker.word(), },
                      {'order': 2, 'value': faker.word(), },
                      ]

        data = dict(ftype=FieldTypes.CLASSIFICATION,
                    name=faker.word(),
                    classification=fclass_set,
                    )

        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_patch_fclass_with_deletion(self):
        """test also, if deletion works"""
        self.profile.can_edit_basedata = True
        self.profile.save()

        field_typ = FieldTypeFactory(ftype=FieldTypes.CLASSIFICATION)
        fclass1 = FClassFactory(ftype=field_typ, order=7, value='7')
        fclass2 = FClassFactory(ftype=field_typ, order=42, value='42')

        self.assertEqual(field_typ.fclass_set.count(), 2)

        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': field_typ.pk, }
        formatjson = dict(format='json')

        # patch the fclass-set with new data

        fclass_set = [{'order': 42, 'value': '422', },
                      {'order': 2, 'value': '2', },
                      {'order': 3, 'value': '3', },
                      ]

        patch_data = dict(classification=fclass_set)
        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=patch_data, extra=formatjson)
        self.response_200(msg=response.content)

        # test if fclasses are correctly updated, added and deleted
        new_fclass_set = field_typ.fclass_set.all()
        self.assertEqual(len(new_fclass_set), 3)
        # check if the 7 is deleted
        self.assertQuerysetEqual(new_fclass_set.filter(order=7), [])
        self.assertEqual(new_fclass_set.get(order=42).value, '422')
        self.assertEqual(new_fclass_set.get(order=2).value, '2')
        self.assertEqual(new_fclass_set.get(order=3).value, '3')

        self.profile.can_edit_basedata = False
        self.profile.save()


class TestPlaceFieldAPI(WriteOnlyWithCanEditBaseDataTest, DemoModeReadOnlyTest,
                        TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "placefields"
    factory = PlaceFieldFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        placefield: PlaceField = cls.obj
        infrastructure = placefield.infrastructure.pk
        field_type = placefield.field_type.pk
        data = dict(name=faker.unique.word(),
                    unit=faker.word(),
                    infrastructure=infrastructure,
                    field_type=field_type,
                    sensitive=True)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data.copy()
        cls.patch_data['sensitive'] = False
        cls.patch_data['name'] = faker.unique.word()
