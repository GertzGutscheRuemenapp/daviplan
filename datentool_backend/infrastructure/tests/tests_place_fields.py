from typing import Tuple, Set, List
from collections import OrderedDict

from django.test import TestCase
from django.contrib.gis.geos import Point
from test_plus import APITestCase

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        )
from datentool_backend.api_test import TestAPIMixin, TestPermissionsMixin

from datentool_backend.user.factories import ProfileFactory, ScenarioFactory
from datentool_backend.user.models.profile import Profile
from datentool_backend.infrastructure.models.infrastructures import (
    Infrastructure, InfrastructureAccess, Service)

from datentool_backend.infrastructure.factories import (
    PlaceFactory, CapacityFactory, PlaceFieldFactory, FieldTypeFactory,
    InfrastructureFactory, ServiceFactory)
from datentool_backend.infrastructure.models.places import (
    Place,
    FieldTypes,
    PlaceField,
    PlaceAttribute,
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

        properties = OrderedDict(
            name=faker.word(),
            infrastructure=infrastructure,
            attributes={'age': faker.pyint(), 'surname': faker.name()},
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

        self.client.logout()
        self.client.force_login(pr1.user)
        response = self.get(self.url_key + '-detail', **self.kwargs)
        attrs = response.data['properties']['attributes']
        self.assertDictEqual(attrs, {'harmless': 123})

        self.client.logout()
        self.client.force_login(pr2.user)
        response = self.get(self.url_key + '-detail', **self.kwargs)
        attrs = response.data['properties']['attributes']
        self.assertDictEqual(attrs, attributes)

        self.client.logout()
        self.client.force_login(self.profile.user)

    def setup_place(self) -> Tuple[Profile, Place]:
        pr1 = ProfileFactory(can_edit_basedata=True)
        place: Place = self.obj

        infr: Infrastructure = place.infrastructure
        infr.accessible_by.set([pr1])
        infr.save()

        field1 = PlaceFieldFactory(name='int_field', sensitive=False,
                                   field_type__ftype=FieldTypes.NUMBER,
                                   infrastructure=infr)
        field2 = PlaceFieldFactory(name='text_field', sensitive=False,
                                   field_type__ftype=FieldTypes.STRING,
                                   infrastructure=infr)
        field3 = PlaceFieldFactory(
            name='class_field',
            sensitive=False,
            field_type__ftype=FieldTypes.CLASSIFICATION,
            infrastructure=infr)

        fclass1 = FClassFactory(ftype=field3.field_type,
                                order=1,
                                value='Category_1')
        fclass2 = FClassFactory(ftype=field3.field_type,
                                order=2,
                                value='Category_2')

        attributes = {'int_field': 123,
                      'text_field': 'ABC',
                      'class_field': 'Category_1', }
        place.attributes = attributes
        place.save()

        return pr1, place

    def test_update_attributes(self):
        """Test update of attributes"""
        pr1, place = self.setup_place()

        patch_data = {'name': 'NewName',
                      'attributes': {'int_field': 456,
                                     'text_field': 'DEF',
                                     'class_field': 'Category_2', }
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
        attrs = response.data['properties']['attributes']
        self.compare_data(attrs, patch_data)

        # check if the changed data is really in the database
        response = self.get_check_200(self.url_key + '-detail', pk=place.pk)
        attrs = response.data['properties']['attributes']
        self.compare_data(attrs, patch_data)

        # patch only one value
        patch_data = {'attributes': {'int_field': 678, }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        expected = {'attributes': {'int_field': 678,
                                   'text_field': 'DEF',
                                   'class_field': 'Category_2', }
                    }
        # check the results returned by the view
        attrs = response.data['properties']['attributes']
        self.compare_data(attrs, expected)

        # check if the changed data is really in the database
        response = self.get_check_200(self.url_key + '-detail', pk=place.pk)
        attrs = response.data['properties']['attributes']
        self.compare_data(attrs, expected)

        # check if invalid attributes return a BadRequest
        patch_data = {'attributes': {'integer_field': 456, }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'int_field': '456', }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'text_field': 12.3, }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        patch_data = {'attributes': {'class_field': 'Category_7', }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_400(msg=response.content)

        # this should work
        patch_data = {'attributes': {'class_field': 'Category_1', }}
        response = self.patch(self.url_key + '-detail', pk=place.pk,
                              data=patch_data, extra=dict(format='json'))
        self.response_200(msg=response.content)

        expected = {'attributes': {'int_field': 678,
                                   'text_field': 'DEF',
                                   'class_field': 'Category_1', }
                    }

        attrs = response.data['properties']['attributes']
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
                              attributes=attributes2)

        place_fields = PlaceField.objects.filter(
            infrastructure=place1.infrastructure,
            name__in=['int_field', 'text_field', 'class_field'])

        for place_field in place_fields:
            # deleting the place field should fail,
            # if there are attributes of this place_field
            response = self.delete('placefields-detail', pk=place_field.pk)
            self.response_403(msg=response.content)

        field_name = 'int_field'
        int_field = PlaceField.objects.get(name=field_name,
                                           infrastructure=place1.infrastructure)

        # deleting the place field should cascadedly delete the attribute
        # from the place attributes
        response = self.delete('placefields-detail',
                               pk=int_field.pk,
                               data=dict(force=True))
        self.response_204(msg=response.content)

        place_attributes = PlaceAttribute.objects.filter(
            place__infrastructure=place1.infrastructure, field__name=field_name)
        self.assertQuerysetEqual(
            place_attributes, [], msg=f'{field_name} should be removed from the place attributes')

        field_name = 'text_field'
        text_field = PlaceField.objects.get(name=field_name,
                                            infrastructure=place1.infrastructure)
        # remove the text_field from place1, so there is no text_field defined
        attributes = {'class_field': 'Category_1', }
        place1.attributes = attributes
        place1.save()

        # it should delete the text_field even without force,
        # because it is not referenced any more
        response = self.delete('placefields-detail',
                               pk=text_field.pk,
                               data=dict(force=False))
        self.response_204(msg=response.content)

        field_name = 'class_field'
        class_field = PlaceField.objects.get(name=field_name,
                                             infrastructure=place1.infrastructure)
        # deleting a FClass category should fail,
        # if there are attributes using this category
        fclass1 = FClass.objects.get(ftype=class_field.field_type, value='Category_1')
        response = self.delete('fclasses-detail',
                               pk=fclass1.pk,
                               data=dict(force=False))
        self.response_403(msg=response.content)

        # deleting a FClass category should work with force,
        response = self.delete('fclasses-detail',
                               pk=fclass1.pk,
                               data=dict(force=True))
        self.response_204(msg=response.content)

        # the attribute should have been removed now in place1
        place_attributes = PlaceAttribute.objects.filter(
            place_id=place1.pk, field__name=field_name)
        self.assertQuerysetEqual(
            place_attributes, [], msg=f'{field_name} should be removed from the place attributes')

        #  create a new Category_3
        fclass3 = FClassFactory(ftype=class_field.field_type,
                                order=1,
                                value='Category_3')

        # this is not used, so it should be deleted also without force
        response = self.delete('fclasses-detail',
                               pk=fclass3.pk,
                               data=dict(force=False))
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
                                  expected: List[int] = None):
        data = dict(service=service.id)
        if scenario is not None:
            data['scenario'] = scenario
        if year is not None:
            data['year'] = year
        if place is not None:
            data['place'] = place
        response = self.get(self.capacity_url + '-list',
                            data=data)
        self.response_200(msg=response.content)
        if expected_place_ids is not None:
            self.assertSetEqual({d['place'] for d in response.data},
                                expected_place_ids)
        assert all((d['service'] == service.id for d in response.data))
        if expected is not None:
            self.assertListEqual(
                [d['capacity'] for d in response.data], expected)

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
        data = dict(name=faker.unique.word(),
                    unit=faker.word(),
                    infrastructure=infrastructure,
                    field_type=field_type,
                    sensitive=True)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data.copy()
        cls.patch_data['sensitive'] = False
