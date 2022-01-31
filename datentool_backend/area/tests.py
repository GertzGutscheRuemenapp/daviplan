from unittest import skipIf
import json
from collections import OrderedDict
from django.test import TestCase
from test_plus import APITestCase
from datetime import datetime
import mapbox_vector_tile

from datentool_backend.utils.test_utils import no_connection
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin,
                                        )
from datentool_backend.area.serializers import (MapSymbolSerializer,
                                                SourceSerializer)

from .factories import (WMSLayerFactory,
                        AreaFactory,
                        AreaLevelFactory,
                        SourceFactory,
                        LayerGroupFactory,
                        FClassFactory,
                        )

from .models import (WMSLayer,
                     AreaLevel,
                     Area,
                     FClass,
                     )

from django.urls import reverse
from django.contrib.gis.geos import MultiPolygon, Polygon

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
        print(area)
        print(area.area_level)
        print(repr(area.area_level))


class TestLayerGroupAPI(WriteOnlyWithCanEditBaseDataTest,
                        TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
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
                      TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
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

    @skipIf(no_connection(), 'No Internetconnection available')
    def test_get_capabilities(self):
        data = {'url': ''}
        self.client.logout()
        response = self.post(self.url_key + '-getcapabilities', data=data,
                             extra={'format': 'json'})
        self.assert_http_401_unauthorized(response)

        self.client.force_login(self.profile.user)
        response = self.post(self.url_key + '-getcapabilities', data=data,
                             extra={'format': 'json'})
        self.assert_http_403_forbidden(response)

        self.profile.can_edit_basedata = True
        self.profile.save()

        response = self.post(self.url_key + '-getcapabilities', data=data,
                             extra={'format': 'json'})
        self.assert_http_400_bad_request(response)

        response = self.post(
            self.url_key + '-getcapabilities',
            data={'url': 'sgx.geodatenzentrum.de/wms_clc5_2018'},
            extra={'format': 'json'})
        self.assert_http_400_bad_request(response)

        url = 'https://monitor.ioer.de/cgi-bin/wms?MAP=O06RG_wms'
        response = self.post(
            self.url_key + '-getcapabilities',
            data={'url': url},
            extra={'format': 'json'})
        self.assert_http_200_ok(response)
        # IÖR have not set up a CORS header
        assert(not response.json()['cors'])

        url = 'https://sgx.geodatenzentrum.de/wms_clc5_2018'
        response = self.post(
            self.url_key + '-getcapabilities',
            data={'url': url},
            extra={'format': 'json'})
        self.assert_http_200_ok(response)

        # response is json, convert to dictionary
        response_dict = response.json()
        assert(response_dict['cors'])
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


class TestAreaLevelAPI(WriteOnlyWithCanEditBaseDataTest,
                       TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "arealevels"
    factory = AreaLevelFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        area_level: AreaLevel = cls.obj
        source_data = SourceSerializer(area_level.source).data
        # workaround: for some reason
        source_data['date'] = datetime.strptime(
            source_data['date'], '%Y-%m-%d').strftime('%d.%m.%Y')
        symbol_data = MapSymbolSerializer(area_level.symbol).data

        data = dict(name=faker.word(), order=faker.random_int(),
                    source=source_data, symbol=symbol_data,
                    label_field=faker.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_preset_protection(self):
        url = self.url_key + '-detail'
        formatjson = dict(format='json')

        self.profile.admin_access = True
        self.profile.save()
        self.obj.is_preset = True
        self.obj.save()

        response = self.delete(url, **self.kwargs)
        self.assert_http_403_forbidden(response)

        patch_data = {'name': 'test'}
        response = self.patch(url, **self.kwargs, data=patch_data,
                              extra=formatjson)
        self.assert_http_403_forbidden(response)

        date = datetime.now().strftime('%d.%m.%Y')
        patch_data = {'source': {'source_type': 'WFS', 'date': date}}
        response = self.patch(url, **self.kwargs, data=patch_data,
                              extra=formatjson)
        self.assert_http_403_forbidden(response)

        patch_data = {'source': {'date': date}}
        response = self.patch(url, **self.kwargs, data=patch_data,
                              extra=formatjson)
        self.assert_http_200_ok(response)

        self.obj.is_preset = False
        self.obj.save()
        self.profile.admin_access = False
        self.profile.save()

    def test_symbol_source(self):
        url = self.url_key + '-detail'
        formatjson = dict(format='json')
        self.profile.admin_access = True
        self.profile.save()

        # check if symbol and source are nullable
        patch_data = self.patch_data.copy()
        patch_data['symbol'] = None
        patch_data['source'] = None
        response = self.patch(url, **self.kwargs, data=patch_data,
                              extra=formatjson)
        self.assertIsNone(response.data['symbol'])
        self.assertIsNone(response.data['source'])

        # check if symbol is recreated
        patch_data['symbol'] = {'symbol': 'square'}
        patch_data['source'] = {'source_type': 'WFS'}
        response = self.patch(url, **self.kwargs, data=patch_data,
                              extra=formatjson)
        self.assertEqual(response.data['symbol']['symbol'], 'square')
        self.assertEqual(response.data['source']['source_type'], 'WFS')

        self.profile.admin_access = False
        self.profile.save()

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

    def test_get_tile_view(self):
        area_level1 = AreaLevelFactory(label_field='gen')
        attributes = json.dumps({'gen': 'Area One', })
        area1 = AreaFactory(area_level=area_level1,
                            attributes=attributes)
        geom = MultiPolygon(Polygon(((1475464, 6888464),
                                     (1515686, 6889190),
                                     (1516363, 6864002),
                                     (1475512, 6864389),
                                     (1475464, 6888464))),
                        srid=3857)
        attributes = json.dumps({'gen': 'Area Two', })
        area2 = AreaFactory(area_level=area_level1,
                            geom=geom,
                            attributes=attributes)

        self.obj = area_level1
        # url1 has content, low zoom level (world)
        url1 = reverse('layer-tile', kwargs={'pk': self.obj.pk, 'z': 1,
                                             'x': 0, 'y': 1})
        response = self.get(url1)
        self.assert_http_200_ok(response)
        # decode the vector tile returned
        result = mapbox_vector_tile.decode(response.content)
        features = result[self.obj.name]['features']
        # the properties contain the values for the areas and the labels
        actual = [feature['properties'] for feature in features][0]

        self.assertEqual(area_level1.id, actual['area_level_id'])

        # url2 has content, exact tile with polygon
        url2 = reverse('layer-tile', kwargs={'pk': self.obj.pk, 'z': 10,
                                             'x': 550, 'y': 336})
        response = self.get(url2)
        self.assert_http_200_ok(response)

        # decode the vector tile returned
        result = mapbox_vector_tile.decode(response.content)
        features = result[self.obj.name]['features']
        # the properties contain the values for the areas and the labels
        actual = [feature['properties'] for feature in features][0]
        self.assertEqual(area_level1.id, actual['area_level_id'])

        # url3 has no content, tile doesn't match with polygon
        url3 = reverse('layer-tile', kwargs={'pk': self.obj.pk, 'z': 12,
                                             'x': 2903, 'y': 1345})
        response = self.get(url3)
        self.assert_http_204_no_content(response)


class TestAreaAPI(WriteOnlyWithCanEditBaseDataTest,
                  TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
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


class TestFClassAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fclasses"
    factory = FClassFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        fclass: FClass = cls.obj
        classification = fclass.classification.pk
        data = dict(classification_id=classification,
                    order=faker.unique.pyint(max_value=100),
                    value=faker.unique.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


