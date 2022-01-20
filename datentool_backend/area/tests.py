from collections import OrderedDict
from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        )

from .factories import (MapSymbolsFactory, WMSLayerFactory, AreaFactory,
                        AreaLevelFactory, SourceFactory,
                        LayerGroupFactory)

from .models import (MapSymbol, WMSLayer, SourceTypes,
                     AreaLevel, Area)
from .serializers import MapSymbolsSerializer


from faker import Faker

faker = Faker('de-DE')


class TestAreas(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.wfs_layer = WMSLayerFactory()
        cls.source = SourceFactory()
        cls.area = AreaFactory()
        print(cls.area)
        print(cls.wfs_layer)

    def test_area(self):
        area = self.area
        print(area.area_level)
        print(repr(area.area_level))


class _TestAPI:
    """test if view and serializer are working correctly """
    url_key = ""
    # replace with concrete factory in sub-class
    factory = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url_pks = dict()
        if cls.factory:
            cls.obj = cls.factory()
            cls.url_pk = dict(pk=cls.obj.pk)


class _TestPermissions():
    """ test users permissions"""
    def test_is_logged_in(self):
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    def test_can_edit_basedata(self):
        profile = self.profile

        original_permission = profile.can_edit_basedata
        original_admin_access = profile.admin_access

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.admin_access = False
        profile.save()
        self.test_post()

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_permission
        profile.admin_access = original_admin_access
        profile.save()

    def admin_access(self):
        profile = self.profile

        original_permission = profile.admin_access

        # Testprofile, with admin_acces
        profile.admin_access = True
        profile.save()
        self.test_post()

        # Testprofile, without admin_acces
        profile.admin_access = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.admin_access = original_permission
        profile.save()


class TestLayerGroupAPI(WriteOnlyWithCanEditBaseDataTest,
                        _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "layergroups"
    factory = LayerGroupFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        existing_order = cls.obj.order
        cls.orders = iter(range(existing_order + 1, 100000))

        cls.post_data = dict(name='posttestname', order=next(cls.orders))
        cls.put_data = dict(name='puttestname', order=next(cls.orders))
        cls.patch_data = dict(name='patchtestname', order=next(cls.orders))


class TestWMSLayerAPI(WriteOnlyWithCanEditBaseDataTest,
                      _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "wmslayers"
    factory = WMSLayerFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        wmslayer: WMSLayer = cls.obj
        group = wmslayer.group.pk
        data = dict(url=faker.url(), name=faker.word(), layer_name=faker.word(),
                    order=faker.random_int(), group=group)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_get_capabilities(self):
        data = {'url': ''}
        self.client.logout()
        response = self.post(self.url_key + '-getcapabilities', data={'url': ''},
                             extra={'format': 'json'})
        self.assert_http_401_unauthorized(response)

        self.client.force_login(self.profile.user)
        response = self.post(self.url_key + '-getcapabilities', data={'url': ''},
                             extra={'format': 'json'})
        self.assert_http_403_forbidden(response)

        self.profile.can_edit_basedata = True
        self.profile.save()

        response = self.post(self.url_key + '-getcapabilities', data={'url': ''},
                             extra={'format': 'json'})
        self.assert_http_400_bad_request(response)

        response = self.post(
            self.url_key + '-getcapabilities',
            data={'url': 'sgx.geodatenzentrum.de/wms_clc5_2018'},
            extra={'format': 'json'})
        self.assert_http_400_bad_request(response)

        url = 'https://sgx.geodatenzentrum.de/wms_clc5_2018'
        response = self.post(
            self.url_key + '-getcapabilities',
            data={'url': url},
            extra={'format': 'json'})
        self.assert_http_200_ok(response)

        # response is json, convert to dictionary
        response_dict = response.json()
        assert 'version' in response_dict
        assert 'layers' in response_dict
        assert 'url' in response_dict
        self.assertURLEqual(response_dict['url'], url)
        layers = response_dict['layers']
        self.assertGreaterEqual(len(layers), 1)
        layer = layers[0]
        # compare the keys of the layer
        self.assertSetEqual(set(layer),
                            {'name', 'title', 'abstract', 'bbox'})
        bbox = layer['bbox']
        self.assertEqual(len(bbox), 4)
        for coord in bbox:
            self.assertIsInstance(coord, float)


class TestSourceAPI(WriteOnlyWithCanEditBaseDataTest,
                    _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """api test Layer"""
    url_key = "sources"
    factory = SourceFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(source_type=faker.random_element(SourceTypes),
                date=faker.date(), id_field=faker.uuid4(), url=faker.url(),
                layer=faker.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestAreaLevelAPI(WriteOnlyWithCanEditBaseDataTest,
                       _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "arealevels"
    factory = AreaLevelFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        area_level: AreaLevel = cls.obj
        source_data = SourceSerializer(area_level.source).data
        layer = area_level.layer.pk

        data = dict(name=faker.word(), order=faker.random_int(),
                    source=source_data, layer=layer)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_assert_response_equals_expected(self):
        expected = OrderedDict(a=1, b=2, c=3)
        response_value = OrderedDict(c=3, b=2, a=1)
        self.assert_response_equals_expected(response_value, expected)

        response_value['b'] = -1
        with self.assertRaises(AssertionError):
            self.assert_response_equals_expected(response_value, expected)

        del response_value['b']
        with self.assertRaises(AssertionError):
            self.assert_response_equals_expected(response_value, expected)

        response_value['b'] = 2
        self.assert_response_equals_expected(response_value, expected)

        response_value['d'] = 99
        with self.assertRaises(AssertionError):
            self.assert_response_equals_expected(response_value, expected)

        expected = '4'
        response_value = 4
        self.assert_response_equals_expected(response_value, expected)

        expected = 4
        response_value = 4
        self.assert_response_equals_expected(response_value, expected)

        expected = 4.0
        response_value = '4'
        with self.assertRaises(AssertionError):
            self.assert_response_equals_expected(response_value, expected)


class TestAreaAPI(WriteOnlyWithCanEditBaseDataTest,
                  _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "areas"
    factory = AreaFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        area: Area = cls.obj
        area_level = area.area_level.pk
        geom = area.geom.ewkt
        properties = OrderedDict(
            area_level=area_level,
            attributes=faker.json(),
        )
        geojson = {
            'type': 'Feature',
            'geometry': geom,
            'properties': properties,
        }

        cls.post_data = geojson
        geojson_put = geojson.copy()
        geojson_put['id'] = area.id
        cls.put_data = geojson_put

        geojson_patch = geojson.copy()
        geojson_patch['geometry'] = area.geom.transform(25832, clone=True).ewkt
        cls.patch_data = geojson_patch
        cls.expected_patch_data = {'geometry': area.geom.ewkt,}


