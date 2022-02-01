from typing import Tuple, Set, List
from collections import OrderedDict
import json

from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Point

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        )
from datentool_backend.api_test import TestAPIMixin, TestPermissionsMixin

from datentool_backend.user.factories import (ProfileFactory,
                                              InfrastructureFactory,
                                              ServiceFactory,
                                              )
from datentool_backend.user.models import (Profile,
                                           Infrastructure,
                                           InfrastructureAccess,
                                           Service,
                                           )


from datentool_backend.infrastructure.factories import (
    ScenarioFactory,
    PlaceFactory,
    CapacityFactory,
    PlaceFieldFactory,
    FieldTypeFactory
)
from datentool_backend.infrastructure.models import (
    Place,
    FieldTypes,
    PlaceField,
)
from datentool_backend.area.factories import FClassFactory
from datentool_backend.area.models import FClass

from faker import Faker
faker = Faker('de-DE')


class TestCapacity(TestCase):

    def test_capacity(self):
        """"""
        infrastructure = InfrastructureFactory()
        capacity = CapacityFactory(place__infrastructure=infrastructure,
                                   service__infrastructure=infrastructure)
        print(capacity)
        print(capacity.place)

    def test_fclass(self):
        """"""
        fclass = FClassFactory()
        print(fclass)

    def test_place_field(self):
        """"""
        place_field = PlaceFieldFactory()
        print(place_field)


class TestPlaceAPI(WriteOnlyWithCanEditBaseDataTest,
                   TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "places"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = PlaceFactory(attributes=faker.json(
            num_rows=1, data_columns={'age': 'pyint', 'surname': 'name'}))

        place: Place = cls.obj
        infrastructure = place.infrastructure.pk

        ft_age = FieldTypeFactory(ftype=FieldTypes.NUMBER)
        field1 = PlaceFieldFactory(
            attribute='age',
            infrastructure=place.infrastructure,
            field_type=ft_age,
            sensitive=False,
        )

        ft_name = FieldTypeFactory(ftype=FieldTypes.STRING)
        field2 = PlaceFieldFactory(
            attribute='surname',
            infrastructure=place.infrastructure,
            field_type=ft_name,
            sensitive=False,
        )

        geom = place.geom.ewkt

        properties = OrderedDict(
            name=faker.word(),
            infrastructure=infrastructure,
            attributes=faker.json(num_rows=1,
                                  data_columns={'age': 'pyint', 'surname': 'name'}),
        )
        geojson = {
            'type': 'Feature',
            'geometry': geom,
            'properties': properties,
        }

        cls.post_data = geojson
        geojson_put = geojson.copy()
        geojson_put['id'] = place.id
        cls.put_data = geojson_put

        geojson_patch = geojson_put.copy()
        pnt = Point(x=10, y=50, srid=4326)
        geojson_patch['geometry'] = pnt.ewkt

        expected_patched = {'geometry': pnt.transform(3857, clone=True).ewkt}

        cls.patch_data = geojson_patch
        cls.expected_patch_data = expected_patched

    def test_sensitive_data(self):
        """Test if sensitive data is correctly shown"""
        pr1 = ProfileFactory()
        pr2 = ProfileFactory()
        place: Place = self.obj
        attributes = {'harmless': 123, 'very_secret': 456, }
        place.attributes = json.dumps(attributes)
        place.save()
        infr: Infrastructure = place.infrastructure
        infr.accessible_by.set([pr1, pr2])
        infr.save()

        i1 = InfrastructureAccess.objects.get(infrastructure=infr, profile=pr1)
        i1.allow_sensitive_data = False
        i1.save()

        i2 = InfrastructureAccess.objects.get(infrastructure=infr, profile=pr2)
        i2.allow_sensitive_data = True
        i2.save()

        field_type = FieldTypeFactory(ftype=FieldTypes.NUMBER)
        field1 = PlaceFieldFactory(attribute='harmless', sensitive=False,
                                   field_type=field_type,
                                   infrastructure=infr)
        field2 = PlaceFieldFactory(attribute='very_secret', sensitive=True,
                                   field_type=field_type,
                                   infrastructure=infr)

        self.client.logout()
        self.client.force_login(pr1.user)
        response = self.get(self.url_key + '-detail', **self.kwargs)
        attrs = json.loads(response.data['properties']['attributes'])
        self.assertDictEqual(attrs, {'harmless': 123})

        self.client.logout()
        self.client.force_login(pr2.user)
        response = self.get(self.url_key + '-detail', **self.kwargs)
        attrs = json.loads(response.data['properties']['attributes'])
        self.assertDictEqual(attrs, attributes)

        self.client.logout()
        self.client.force_login(self.profile.user)

    def setup_place(self) -> Tuple[Profile, Place]:
        pr1 = ProfileFactory(can_edit_basedata=True)
        place: Place = self.obj
        attributes = {'int_field': 123,
                      'text_field': 'ABC',
                      'class_field': 'Category_1', }
        place.attributes = json.dumps(attributes)
        place.save()
        infr: Infrastructure = place.infrastructure
        infr.accessible_by.set([pr1])
        infr.save()

        field1 = PlaceFieldFactory(attribute='int_field', sensitive=False,
                                   field_type__ftype=FieldTypes.NUMBER,
                                   infrastructure=infr)
        field2 = PlaceFieldFactory(attribute='text_field', sensitive=False,
                                   field_type__ftype=FieldTypes.STRING,
                                   infrastructure=infr)
        field3 = PlaceFieldFactory(
            attribute='class_field',
            sensitive=False,
            field_type__ftype=FieldTypes.CLASSIFICATION,
            infrastructure=infr)

        fclass1 = FClassFactory(ftype=field3.field_type,
                                order=1,
                                value='Category_1')
        fclass2 = FClassFactory(ftype=field3.field_type,
                                order=2,
                                value='Category_2')
        return pr1, place

    def test_update_attributes(self):
        """Test update of attributes"""
        pr1, place = self.setup_place()

        patch_data = {'name': 'NewName',
                      'attributes': {'int_field': 456,
                                     'text_field': 'DEF',
                                     'class_field': 'Category_2', }
                      }

        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_403(msg=response.content)

        self.client.logout()
        self.client.force_login(pr1.user)

        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        # check the results returned by the view
        attrs = json.loads(response.data['attributes'])
        self.compare_data(attrs, patch_data)

        # check if the changed data is really in the database
        response = self.get_check_200(self.url_key + '-detail', pk=place.pk)
        attrs = json.loads(response.data['properties']['attributes'])
        self.compare_data(attrs, patch_data)

        # patch only one value
        patch_data = {'attributes': {'int_field': 678, }}
        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        expected = {'attributes': {'int_field': 678,
                                   'text_field': 'DEF',
                                   'class_field': 'Category_2', }
                    }
        # check the results returned by the view
        attrs = json.loads(response.data['attributes'])
        self.compare_data(attrs, expected)

        # check if the changed data is really in the database
        response = self.get_check_200(self.url_key + '-detail', pk=place.pk)
        attrs = json.loads(response.data['properties']['attributes'])
        self.compare_data(attrs, expected)

        patch_data = {'attributes': {'integer_field': 456, }}
        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'int_field': '456', }}
        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'text_field': 12.3, }}
        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'class_field': 'Category_7', }}
        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'class_field': 'Category_1', }}
        response = self.patch(self.url_key + '-update-attributes', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        expected = {'attributes': {'int_field': 678,
                                   'text_field': 'DEF',
                                   'class_field': 'Category_1', }
                    }

        attrs = json.loads(response.data['attributes'])
        self.compare_data(attrs, patch_data)

    def test_delete_placefield_and_fclass(self):
        """
        Test, if the deletion of a PlaceField
        and a FClass cascades to the Place Attributes
        """
        profile, place1 = self.setup_place()
        self.client.logout()
        self.client.force_login(profile.user)

        attributes2 = {'int_field': 789,
                       'class_field': 'Category_2', }
        place2 = PlaceFactory(infrastructure=place1.infrastructure,
                              attributes=json.dumps(attributes2))

        place_fields = PlaceField.objects.filter(
            infrastructure=place1.infrastructure,
            attribute__in=['int_field', 'text_field', 'class_field'])

        for place_field in place_fields:
            # deleting the place field should fail,
            # if there are attributes of this place_field
            response = self.delete('placefields-detail', pk=place_field.pk)
            self.response_403(msg=response.content)

        field_name = 'int_field'
        int_field = PlaceField.objects.get(attribute=field_name,
                                           infrastructure=place1.infrastructure)

        # deleting the place field should cascadedly delete the attribute
        # from the place attributes
        response = self.delete('placefields-detail',
                               pk=int_field.pk,
                               data=dict(override_protection=True))
        self.response_204(msg=response.content)

        place_attributes = Place.objects.filter(
            infrastructure=place1.infrastructure).values_list('attributes',
                                                              flat=True)
        for attr in place_attributes:
            attr_dict = json.loads(attr)
            msg = f'{field_name} should be removed from the place attributes {attr_dict}'
            self.assertFalse(field_name in attr_dict, msg)

        field_name = 'text_field'
        text_field = PlaceField.objects.get(attribute=field_name,
                                            infrastructure=place1.infrastructure)
        # remove the text_field from place1, so there is no text_field defined
        attributes = {'class_field': 'Category_1', }
        place1.attributes = json.dumps(attributes)
        place1.save()

        # it should delete the text_field even without override_protection,
        # because it is not referenced any more
        response = self.delete('placefields-detail',
                               pk=text_field.pk,
                               data=dict(override_protection=False))
        self.response_204(msg=response.content)

        field_name = 'class_field'
        class_field = PlaceField.objects.get(attribute=field_name,
                                             infrastructure=place1.infrastructure)
        # deleting a FClass category should fail,
        # if there are attributes using this category
        fclass1 = FClass.objects.get(ftype=class_field.field_type, value='Category_1')
        response = self.delete('fclasses-detail',
                               pk=fclass1.pk,
                               data=dict(override_protection=False))
        self.response_403(msg=response.content)

        # deleting a FClass category should work with override_protection,
        response = self.delete('fclasses-detail',
                               pk=fclass1.pk,
                               data=dict(override_protection=True))
        self.response_204(msg=response.content)

        # the attribute should have been removed now in place1
        place_attributes = Place.objects.get(pk=place1.pk).attributes
        attr_dict = json.loads(place_attributes)
        msg = f'{field_name} should be removed from the place attributes {attr_dict}'
        self.assertFalse(field_name in attr_dict, msg)

        #  create a new Category_3
        fclass3 = FClassFactory(classification=class_field.field_type,
                                order=1,
                                value='Category_3')

        # this is not used, so it should be deleted also without override_protection
        response = self.delete('fclasses-detail',
                               pk=fclass3.pk,
                               data=dict(override_protection=False))
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

        #  default capacity has from_year=0 and capacity=0
        # add two more capacities
        CapacityFactory(service=service3, place=place2,
                        from_year=2023, capacity=123)
        CapacityFactory(service=service3, place=place2,
                        from_year=2021, capacity=55)

        #  test if the correct places which offer a service are returned
        self.check_place_with_capacity(service1, {place1.id})
        self.check_place_with_capacity(service2, {place1.id, place2.id})
        self.check_place_with_capacity(service3, {place2.id})

        year_expected = {2020: 0,
                         2021: 55,
                         2022: 55,
                         2023: 123,
                         2024: 123,
                         }

        #  test if the correct capacity is returned for different years
        for year, expected in year_expected.items():
            response = self.get(self.url_key + '-detail', pk=place2.pk,
                                data=dict(service=service3.id, year=year))
            capacity = response.data['properties']['capacity']
            #  Todo: check if frontend needs the whole capacity information
            # or only the capacity values
            self.assertListEqual([c['capacity'] for c in capacity], [expected])
            self.assertListEqual(response.data['properties']['capacities'],
                                 [expected])

        #  without the year
        response = self.get(self.url_key + '-detail', pk=place2.pk,
                            data=dict(service=service3.id))
        capacity = response.data['properties']['capacity']
        self.assertListEqual([c['capacity'] for c in capacity], [0])

        #  this should fail, because there is no service3 offered at place1
        response = self.get(self.url_key + '-detail', pk=place1.pk,
                            data=dict(service=service3.id, year=2024))
        self.response_404(response)

    def check_place_with_capacity(self, service: Service,
                                  place_ids: Set[int],
                                  year: int = None):
        response = self.get(self.url_key + '-list',
                            data=dict(service=service.id))
        self.response_200(msg=response.content)
        self.assertSetEqual({p['id'] for p in response.data['features']},
                            place_ids)
        feature_capacities = [f['properties']['capacity']
                              for f in response.data['features']]
        for fc in feature_capacities:
            assert all((c['service'] == service.id for c in fc))

    def test_check_capacity_for_scenario(self):
        scenario1 = ScenarioFactory()
        scenario2 = ScenarioFactory(planning_process=scenario1.planning_process)
        scenario3 = ScenarioFactory(planning_process=scenario1.planning_process)

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
        self.check_capacity_detail([50], place1.pk, service1.pk)
        self.check_capacity_detail([99], place1.pk, service2.pk)
        self.check_capacity_detail([50, 99], place1.pk)

        #  In scenario1, it should change
        self.check_capacity_detail([100], place1.pk, service1.pk,
                                   scenario_id=scenario1.pk)
        #  In scenario2, no new capacity defined,
        # so take the base value for the base year
        self.check_capacity_detail([50], place1.pk, service1.pk,
                                   scenario_id=scenario2.pk)
        #  .. and the base-scenario value vor year 2026
        self.check_capacity_detail([77], place1.pk, service1.pk,
                                   scenario_id=scenario2.pk, year=2026)
        #  In scenario3, it should change over time from 100 over 200 to 0
        self.check_capacity_detail([100], place1.pk, service1.pk,
                                   scenario_id=scenario3.pk, year=2021)
        self.check_capacity_detail([200], place1.pk, service1.pk,
                                   scenario_id=scenario3.pk, year=2022)
        self.check_capacity_detail([200], place1.pk, service1.pk,
                                   scenario_id=scenario3.pk, year=2025)
        self.check_capacity_detail([0], place1.pk, service1.pk,
                                   scenario_id=scenario3.pk, year=2030)

        CapacityFactory(place=place2, service=service1, capacity=88)
        CapacityFactory(place=place2, service=service1, from_year=2022, capacity=99)
        CapacityFactory(place=place2, service=service1, scenario=scenario1, capacity=55)
        CapacityFactory(place=place2, service=service1, scenario=scenario2, capacity=33)

        self.check_capacity_list([50, 88], service1.pk)
        self.check_capacity_list([50, 99], service1.pk, year=2023)
        self.check_capacity_list([77, 99], service1.pk, year=2026)
        self.check_capacity_list([100, 55], service1.pk, scenario_id=scenario1.pk)
        self.check_capacity_list([50, 33], service1.pk, scenario_id=scenario2.pk)
        self.check_capacity_list([100, 88], service1.pk, scenario_id=scenario3.pk)

    def check_capacity_detail(self,
                              expected: float,
                              place_id: int,
                              service_id: int = None,
                              year: int = None,
                              scenario_id: int = None):
        query_params = {}
        if service_id:
            query_params['service'] = service_id
        if year:
            query_params['year'] = year
        if scenario_id:
            query_params['scenario'] = scenario_id
        response = self.get(self.url_key + '-detail', pk=place_id,
                            data=query_params)
        self.assertListEqual(response.data['properties']['capacities'],
                             expected)

    def check_capacity_list(self,
                            expected: List[int],
                            service_id: int = None,
                            year: int = None,
                            scenario_id: int = None,
                            ):
        query_params = {}
        if service_id:
            query_params['service'] = service_id
        if year:
            query_params['year'] = year
        if scenario_id:
            query_params['scenario'] = scenario_id

        response = self.get_check_200(self.url_key + '-list', data=query_params)
        self.assertListEqual(
            [f['properties']['capacities'][0] for f in response.data['features']],
            expected)


class TestCapacityAPI(WriteOnlyWithCanEditBaseDataTest,
                      TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "capacities"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        infrastructure = InfrastructureFactory()
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


class TestFieldTypeNUMSTRAPI(WriteOnlyWithCanEditBaseDataTest,
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


class TestFieldTypeCLAAPI(WriteOnlyWithCanEditBaseDataTest,
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


class TestPlaceFieldAPI(WriteOnlyWithCanEditBaseDataTest,
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
        data = dict(attribute=faker.unique.word(),
                    unit=faker.word(),
                    infrastructure=infrastructure,
                    field_type=field_type,
                    sensitive=True)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data.copy()
        cls.patch_data['sensitive'] = False
