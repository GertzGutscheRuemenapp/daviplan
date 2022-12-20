from django.test import TestCase
from test_plus import APITestCase
from unittest import skip
import logging
logger = logging.getLogger(name='test')

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        WriteOnlyWithAdminAccessTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin)
from datentool_backend.area.serializers import MapSymbolSerializer

from datentool_backend.user.factories import ProfileFactory
from datentool_backend.infrastructure.factories import (InfrastructureFactory,
                                                        ServiceFactory,)
from datentool_backend.area.factories import FieldTypeFactory, FieldType
from datentool_backend.area.models import FieldTypes
from datentool_backend.infrastructure.models import Infrastructure, Service

from faker import Faker
faker = Faker('de-DE')


class TestInfrastructure(TestCase):

    def test_service(self):
        service = ServiceFactory()
        logger.debug(service.quota_type)

    def test_infrastructure(self):
        """"""
        profiles = [ProfileFactory() for i in range(3)]
        infrastructure = InfrastructureFactory(editable_by=profiles[:2],
                                               accessible_by=profiles[1:])
        self.assertQuerysetEqual(infrastructure.editable_by.all(),
                                 profiles[:2], ordered=False)
        self.assertQuerysetEqual(infrastructure.accessible_by.all(),
                                 profiles[1:], ordered=False)


class TestInfrastructureAPI(WriteOnlyWithAdminAccessTest,
                            TestPermissionsMixin, TestAPIMixin,
                            BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "infrastructures"
    factory = InfrastructureFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cl_ft1 = FieldTypeFactory(ftype=FieldTypes.STRING, name='Zeichenkette')
        infrastructure: Infrastructure = cls.obj
        editable_by = list(infrastructure.editable_by.all().values_list(flat=True))
        accessible_by = [{'profile': p, 'allow_sensitive_data': True}
                         for p in
                         infrastructure.accessible_by.all().values_list(flat=True)]
        symbol_data = MapSymbolSerializer(infrastructure.symbol).data

        data = dict(name=faker.word(),
                    description=faker.word(),
                    order=faker.pyint(max_value=10),
                    editable_by=editable_by,
                    accessible_by=accessible_by,
                    symbol=symbol_data)
        cls.post_data = data
        cls.put_data = data
        #  for patch, test if different value for allow_sensitive_data is passed
        cls.patch_data = data.copy()
        accessible_by = [{'profile': p, 'allow_sensitive_data': False}
                         for p in
                         infrastructure.accessible_by.all().values_list(flat=True)]
        cls.patch_data['accessible_by'] = accessible_by

    def test_patch_empty_editable_by(self):
        """Test the patch with an empty list"""
        patch_data2 = self.patch_data.copy()
        patch_data2['editable_by'] = []
        #patch_data2['accessible_by'] = []
        self.patch_data = patch_data2
        super().test_put_patch()

    @skip('is replaced by test_can_patch_symbol')
    def test_can_edit_basedata(self):
        pass

    def test_admin_access(self):
        """write permission if user has admin_access"""
        super().admin_access()

    def test_can_patch_layer(self):
        """
        user, who can_edit_basedata has permission
        to patch the layer with its symbol
        """
        profile = self.profile
        permission_basedata = profile.can_edit_basedata
        permission_admin = profile.admin_access

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.admin_access = False
        profile.save()

        # test post
        url = self.url_key + '-list'

        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

        # test put
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)

        # check status code for patch
        self.patch_data = {'symbol': {'symbol': 'line'}}
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_200(msg=response.content)
        self.assertEqual(response.data['symbol']['symbol'], 'line')

        # check if symbol is nullable
        self.patch_data = { 'symbol': None }
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.assertIsNone(response.data['symbol'])

        # check if symbol is recreated
        self.patch_data = {'symbol': {'symbol': 'square'}}
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.assertEqual(response.data['symbol']['symbol'], 'square')

        # Other fields should not be edited
        self.patch_data['description'] = 'A new description'
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        # test post
        url = self.url_key + '-list'
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

        # test put_patch
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        # check status code for put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)

        # check status code for patch
        self.patch_data = {'symbol': {'symbol': 'line'}}

        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

        profile.admin_access = permission_admin
        profile.can_edit_basedata = permission_basedata
        profile.save()

    def test_user_access_list(self):
        """Test the access-list of the user"""
        profile = ProfileFactory(admin_access=True)
        self.client.logout()
        self.client.force_login(user=profile.user)
        infra1 = InfrastructureFactory(accessible_by=[profile])
        infra2 = InfrastructureFactory(accessible_by=[profile])
        infra3: Infrastructure = self.obj
        infra_access = infra1.infrastructureaccess_set.first()
        infra_access.allow_sensitive_data = True
        infra_access.save()
        response = self.get('users-detail', pk=profile.user.pk)
        expected = [{'infrastructure': infra1.id, 'allowSensitiveData': True},
                    {'infrastructure': infra2.id, 'allowSensitiveData': False}]
        self.compare_data(response.data['access'], expected)

        patch_data = {'access':
                      [{'infrastructure': infra3.id, 'allowSensitiveData': True}]}
        response = self.patch('users-detail', pk=profile.user.pk, data=patch_data,
                              extra=dict(format='json'))
        self.response_200(response)
        response = self.get('users-detail', pk=profile.user.pk)
        expected = [{'infrastructure': infra3.id, 'allowSensitiveData': True}]
        self.compare_data(response.data['access'], expected)

    def test_create_infrastructure_with_placefields(self):
        """create a new infrastructure with placefields"""
        self.profile.admin_access = True
        self.profile.save()
        self.client.force_login(self.profile.user)
        url = self.url_key + '-list'
        formatjson = dict(format='json')


        data = self.post_data.copy()
        ft_str = FieldType.objects.get(name='Zeichenkette')
        ft_num = FieldTypeFactory.create(ftype=FieldTypes.NUMBER, name='Zahl')

        # create 2 fields with the same name
        placefields = [{'name': 'A', 'field_type': ft_str.pk, },
                       {'name': 'A', 'field_type': ft_num.pk, },
                       ]
        data['place_fields'] = placefields
        # same names are not allowed
        res = self.post(url, data=data, extra=formatjson)
        self.assert_http_406_not_acceptable(res)

        # Underscores in names are not allowed
        data['place_fields'][1]['name'] = 'A_'
        res = self.post(url, data=data, extra=formatjson)
        self.assert_http_406_not_acceptable(res)

        # field names that are in the presets (ignoring capitals) are not allowed
        data['place_fields'][1]['name'] = 'plz'
        res = self.post(url, data=data, extra=formatjson)
        self.assert_http_406_not_acceptable(res)

        # Distict names without underscores are allowed
        pf2 = data['place_fields'][1]
        pf2['name'] = 'B'
        pf2['unit'] = 'ha'
        pf2['label'] = 'Hectar'
        pf2['sensitive'] = True
        res = self.post(url, data=data, extra=formatjson)
        self.assert_http_201_created(res)

        # check if the created place_fields are correctly created
        infra_pk = res.data['id']
        infra = Infrastructure.objects.get(pk=infra_pk)
        preset_fields = infra.placefield_set.filter(is_preset=True)
        self.assertEqual(len(preset_fields), 4)
        custom_fields = infra.placefield_set.filter(is_preset=False)
        fields_a = custom_fields.filter(name='A')
        self.assertEqual(len(fields_a), 1)
        fields_b = custom_fields.filter(name='B')
        self.assertEqual(len(fields_b), 1)
        field_b = fields_b[0]
        self.assertEqual(field_b.unit, pf2['unit'])
        self.assertEqual(field_b.label, pf2['label'])
        self.assertEqual(field_b.sensitive, pf2['sensitive'])
        self.assertEqual(field_b.field_type_id, pf2['field_type'])

        # update the placefields of the infrastructure
        patch_data = {'place_fields': placefields, }
        # delete field A by not including it in the patch data
        pf1 = placefields.pop(0)
        # set id to field b and change unit
        pf2['id'] = field_b.pk
        pf2['name'] = 'ort'
        pf2['unit'] = 'km'

        # add a new field
        placefields.append({'name': 'C', 'unit': 'm2', 'field_type': ft_num.pk})

        # name already exists (in capital letters)
        res = self.patch(self.url_key + '-detail',
                         pk=infra.pk,
                         data=patch_data,
                         extra=formatjson)
        self.assert_http_406_not_acceptable(res)

        pf2['name'] = 'B'
        res = self.patch(self.url_key + '-detail',
                         pk=infra.pk,
                         data=patch_data,
                         extra=formatjson)
        self.assert_http_200_ok(res)


        # preset fields should be untouched
        preset_fields = infra.placefield_set.filter(is_preset=True)
        self.assertEqual(len(preset_fields), 4)

        custom_fields = infra.placefield_set.filter(is_preset=False)
        # field a should be deleted now
        fields_a = custom_fields.filter(name='A')
        self.assertEqual(len(fields_a), 0)
        # field b should have a new unit
        fields_b = custom_fields.filter(name='B')
        self.assertEqual(len(fields_b), 1)
        field_b = fields_b[0]
        self.assertEqual(field_b.unit, pf2['unit'])

        # field c sould be created
        fields_c = custom_fields.filter(name='C')
        self.assertEqual(len(fields_c), 1)
        field_c = fields_c[0]
        self.assertEqual(field_c.unit, 'm2')


class TestServiceAPI(WriteOnlyWithCanEditBaseDataTest,
                     TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "services"
    factory = ServiceFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        service: Service = cls.obj
        infrastructure = service.infrastructure.pk
        editable_by = list(service.editable_by.all().values_list(flat=True))

        data = dict(name=faker.word(),
                    description=faker.word(),
                    infrastructure=infrastructure,
                    editable_by=editable_by,
                    capacity_singular_unit=faker.word(),
                    capacity_plural_unit=faker.word(),
                    has_capacity=True,
                    demand_singular_unit=faker.word(),
                    demand_plural_unit=faker.word(),
                    quota_type=faker.word(),
                    demand_name=faker.word(),
                    demand_description=faker.word(),
                    facility_singular_unit = faker.word(),
                    facility_article = faker.word(),
                    facility_plural_unit = faker.word(),
                    direction_way_relationship = faker.pyint(max_value=2, min_value=1)
                    )
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

