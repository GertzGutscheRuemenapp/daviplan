from unittest import skipIf
from collections import OrderedDict
from django.test import TestCase
from django.db.utils import IntegrityError
from test_plus import APITestCase
from datetime import datetime
import mapbox_vector_tile

from datentool_backend.utils.test_utils import no_connection
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin,
                                        LoginTestCase
                                        )
from datentool_backend.area.serializers import (MapSymbolSerializer,
                                                SourceSerializer)

from datentool_backend.area.factories import (WMSLayerFactory,
                                              AreaFactory,
                                              AreaLevelFactory,
                                              AreaFieldFactory,
                                              SourceFactory,
                                              LayerGroupFactory,
                                              FClassFactory,
                                              SourceFactory
                                              )

from datentool_backend.area.models import (WMSLayer,
                                           AreaLevel,
                                           Area,
                                           FClass,
                                           AreaField,
                                           AreaAttribute,
                                           FieldType,
                                           FieldTypes,
                                           SourceTypes
                                           )
from datentool_backend.site.factories import ProjectSettingFactory

from django.urls import reverse
from django.contrib.gis.geos import MultiPolygon, Polygon

from faker import Faker

faker = Faker('de-DE')


class TestWfs(LoginTestCase, APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.admin_access = True
        cls.profile.save()
        source = SourceFactory(
            url='https://sgx.geodatenzentrum.de/wfs_vg250',
            layer='vg250_gem',
            source_type=SourceTypes.WFS
        )
        cls.area_level = AreaLevelFactory(source=source, is_preset=True)
        AreaFieldFactory(name='gen',
                         area_level=cls.area_level,
                         field_type__ftype=FieldTypes.STRING,
                         is_label=True)
        AreaFieldFactory(name='ags',
                         area_level=cls.area_level,
                         field_type__ftype=FieldTypes.STRING,
                         is_key=True)
        source = SourceFactory(
            source_type=SourceTypes.FILE
        )
        cls.area_level_no_wfs = AreaLevelFactory(source=source)

        # area around Lübeck
        ewkt = 'SRID=3857;MULTIPOLYGON(((1152670 7165895, 1205564 7165895, 1205564 7114543, 1152670 7114543, 1152670 7165895)))'
        geom = MultiPolygon.from_ewkt(ewkt)
        ProjectSettingFactory(project_area=geom)

    def test_pull_areas(self):
        response = self.post('arealevels-pull-areas',
                             pk=self.area_level_no_wfs.id)
        self.assert_http_406_not_acceptable(response)

        response = self.post('arealevels-pull-areas', pk=self.area_level.id)
        self.assert_http_202_accepted(response)
        areas = Area.objects.filter(area_level=self.area_level)
        # ToDo: test intersection with project area?
        # (e.g. comparing bbox with project bbox or
        # joining areas and difference.area < sth)
        labels = set([a.label for a in areas])
        self.assertGreater(len(labels), 1)
        # test for uniqueness
        keys = set([a.key for a in areas])
        self.assertEqual(len(keys), len(areas))
        # ToDo: test permissions
        # ToDo: test 'truncate' and 'simplify' query params
        # ToDo: test intersect with raster and aggregation?
        # (setup raster and popultions required)


class TestAreas(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.wfs_layer = WMSLayerFactory()
        cls.source = SourceFactory()
        fclass1 = FClassFactory(value='Class1')
        fclass2 = FClassFactory(ftype=fclass1.ftype, value='Class2')
        cls.area = AreaFactory()
        area_level: AreaLevel = cls.area.area_level
        classfield = AreaField.objects.create(name='classfield',
                                              area_level=area_level,
                                              field_type=fclass1.ftype)
        cls.area2 = AreaFactory(
            area_level=area_level,
            attributes={'areaname': 'MyName', 'Inhabitants': 123,
                        'classfield': 'Class2', 'ags': '01234', })
        name_field = area_level.areafield_set.get(name='areaname')
        name_field.is_label = True
        name_field.save()
        key_field = area_level.areafield_set.get(name='ags')
        key_field.is_key = True
        key_field.save()
        print(cls.area)
        print(cls.wfs_layer)

    def test_area(self):
        area = self.area
        print(area)
        print(area.area_level)
        print(repr(area.area_level))

    def test_area_attributes(self):
        area1: Area = self.area
        area2: Area = self.area2

        aa = AreaAttribute.objects.filter(area=area2)
        self.assertEqual(aa.get(field__name='areaname').value, 'MyName')
        self.assertEqual(aa.get(field__name='Inhabitants').value, 123)
        self.assertEqual(aa.get(field__name='classfield').value, 'Class2')

        #  test the annotated value
        aa = AreaAttribute.value_annotated_qs().filter(area=area2)
        self.assertEqual(aa.get(field__name='areaname')._value, 'MyName')
        self.assertEqual(aa.get(field__name='Inhabitants')._value, '123')
        self.assertEqual(aa.get(field__name='classfield')._value, 'Class2')
        self.assertEqual(aa.get(field__name='classfield').value, 'Class2')

        # test setting the area attribute
        with self.assertRaises(ValueError):
            aa.get(field__name='classfield').value = 'Class3'

        aa.get(field__name='classfield').value = 'Class1'
        aa.get(field__name='classfield').value = 'Class2'
        print(aa)

        #  test the labels
        area_level: AreaLevel = area1.area_level
        self.assertEqual(area_level.label_field, 'areaname')
        self.assertEqual(area2.label, 'MyName')
        self.assertEqual(area1.label, '')
        self.assertEqual(area2.key, '01234')
        self.assertEqual(area1.key, '')

        # areaname should be a string field
        name_field = area_level.areafield_set.get(name='areaname')
        self.assertEqual(name_field.field_type.ftype, 'STR')

        # inhabitant_field should be a num-field
        inh_field = area_level.areafield_set.get(name='Inhabitants')
        self.assertEqual(inh_field.field_type.ftype, 'NUM')

        # classfield should be a class field
        class_field = area_level.areafield_set.get(name='classfield')
        self.assertEqual(class_field.field_type.ftype, 'CLA')
        self.assertEqual(area2.get_attr_value('classfield'), 'Class2')

        # change label field to num_field
        name_field.is_label = False
        inh_field.is_label = True
        name_field.save()
        inh_field.save()
        self.assertEqual(float(area2.label), 123)
        self.assertEqual(area1.label, '')

        # setting another field as label field should raise an error
        with self.assertRaises(IntegrityError):
            name_field.is_label = True
            name_field.save()

    def test_area_label(self):
        """Test the area label and attribute values"""
        areas = Area.objects.all()
        self.assertEqual(areas[0].label, '')
        self.assertEqual(areas[1].label, 'MyName')

        areas = Area.label_annotated_qs(area_level=self.area.area_level).all()
        self.assertEqual(areas[0].label, None)
        self.assertEqual(areas[1].label, 'MyName')
        self.assertEqual(areas[1]._label, 'MyName')


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

        url = 'https://sgx.geodatenzentrum.de/wms_landschaften'
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
        symbol_data = MapSymbolSerializer(area_level.symbol).data

        data = dict(name=faker.word(), order=faker.random_int(),
                    source=source_data, symbol=symbol_data)
        source_data['date'] = datetime.strptime(
            source_data['date'], '%Y-%m-%d').strftime('%d.%m.%Y')
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
        area_level1 = AreaLevelFactory()
        str_field = FieldType.objects.create(name='str_field',
                                             ftype=FieldTypes.STRING)
        name_field = AreaField.objects.create(area_level=area_level1,
                                              field_type=str_field,
                                              name='gen',
                                              is_label=True)
        area1 = AreaFactory(area_level=area_level1,
                            attributes={'gen': 'Area One', })

        self.assertEqual(area1.label, 'Area One')

        geom = MultiPolygon(Polygon(((1475464, 6888464),
                                     (1515686, 6889190),
                                     (1516363, 6864002),
                                     (1475512, 6864389),
                                     (1475464, 6888464))),
                        srid=3857)
        area1 = AreaFactory(area_level=area_level1,
                            geom=geom)
        AreaAttribute.objects.create(area=area1, field=name_field, value='Area One')

        area2 = AreaFactory(area_level=area_level1,
                            geom=geom)
        AreaAttribute.objects.create(area=area2, field=name_field, value='Area Two')

        self.obj = area_level1
        # url1 has content, low zoom level (world)
        url1 = reverse('layer-tile', kwargs={'pk': self.obj.pk, 'z': 1,
                                             'x': 0, 'y': 1})
        response = self.get(url1)
        self.assert_http_200_ok(response)

        result = mapbox_vector_tile.decode(response.content)
        features = result[self.obj.name]['features']
        # the properties contain the values for the areas and the labels
        actual = [feature['properties'] for feature in features][0]

        self.assertEqual(area_level1.id, actual['area_level_id'])

        # url2 has content, exact tile with polygon
        features = result[area_level1.name]['features']
        assert(features[0]['properties']['_label'] == 'Area One')

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
                                             'x': 2903, 'y': 1345}) # 2198
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
        cls.area_level = area_level = area.area_level.pk
        name_field_type = FieldType.objects.create(ftype=FieldTypes.STRING,
                                                   name='name_field')
        int_field_type = FieldType.objects.create(ftype=FieldTypes.NUMBER,
                                                  name='num_field')
        name_field = AreaField.objects.create(area_level=area.area_level,
                                              name='gen',
                                              field_type=name_field_type,
                                              is_label=True)
        key_field = AreaField.objects.create(area_level=area.area_level,
                                              name='ags',
                                              field_type=name_field_type,
                                              is_key=True)
        int_field = AreaField.objects.create(area_level=area.area_level,
                                             name='inhabitants',
                                             field_type=int_field_type)

        aa = AreaAttribute.objects.create(area=area,
                                          field=name_field,
                                          value='A-Town',
                                          )
        aa = AreaAttribute.objects.create(area=area,
                                          field=key_field,
                                          value='012345',
                                          )


        AreaAttribute.objects.create(area=area,
                                     field=int_field,
                                     value=12345)

        geom = area.geom.ewkt
        properties = OrderedDict(
            area_level=area_level,
            attributes={'gen': 'Area32', 'inhabitants': 400, },
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

    def test_is_logged_in(self):
        """Test read, if user is authenticated"""
        self.query_params['area_level'] = self.area_level
        super().test_is_logged_in()
        try:
            del self.query_params['area_level']
        except KeyError:
            pass

    def test_list(self):
        """Test read, if user is authenticated"""
        self.query_params['area_level'] = self.area_level
        super().test_list()
        try:
            del self.query_params['area_level']
        except KeyError:
            pass


class TestFClassAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fclasses"
    factory = FClassFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        fclass: FClass = cls.obj
        classification = fclass.ftype.pk
        data = dict(ftype_id=classification,
                    order=faker.unique.pyint(max_value=100),
                    value=faker.unique.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestAreaFieldAPI(WriteOnlyWithCanEditBaseDataTest,
                        TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "areafields"
    factory = AreaFieldFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        areafield: AreaField = cls.obj
        area_level = areafield.area_level.pk
        field_type = areafield.field_type.pk
        data = dict(name=faker.unique.word(),
                    area_level=area_level,
                    field_type=field_type,
                    is_key=True,
                    is_label=False)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data.copy()
        cls.patch_data['is_key'] = False
