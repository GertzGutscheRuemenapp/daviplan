from collections import OrderedDict
from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
import factory


from .factories import (SymbolFormFactory, MapSymbolsFactory,
                        WMSLayerFactory, InternalWFSLayerFactory,
                        AreaFactory, AreaLevelFactory, SourceFactory,
                        LayerGroupFactory)

from .models import (MapSymbol, WMSLayer, InternalWFSLayer, SourceTypes,
                     AreaLevel, Area)


from faker import Faker

faker = Faker('de-DE')


class TestAreas(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.wfs_layer = WMSLayerFactory()
        cls.layer = InternalWFSLayerFactory()
        cls.source = SourceFactory()
        cls.area = AreaFactory()
        print(cls.area)
        print(cls.wfs_layer)

    def test_area(self):
        area = self.area
        print(area.area_level)
        print(repr(area.area_level))


class _TestAPI:
    """"""
    url_key = ""
    factory = SymbolFormFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.obj = cls.factory()
        cls.url_pks = dict()
        cls.url_pk = dict(pk=cls.obj.pk)


class TestSymbolFormAPI(_TestAPI, BasicModelTest, APITestCase):
    """ test if view and serializer are working correctly """
    url_key = "symbolforms"
    factory = SymbolFormFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_data = dict(name='posttestname')
        cls.put_data = dict(name='puttestname')
        cls.patch_data = dict(name='patchtestname')

    def test_is_logged_in(self):
        """test for permission rights, logged_in user has permission to read"""

        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.assert_http_302_found or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    def test_can_edit_basedata(self):
        """test for permission rights, user who can_edit_basedata has write permission """
        profile = self.profile

        original_permission = profile.can_edit_basedata

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.save()
        self.test_post()

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_201(msg=response.content)

        profile.can_create_process = original_permission
        profile.save()

class TestMapSymbolsAPI(_TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "mapsymbols"
    factory = MapSymbolsFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mapsymbol: MapSymbol = cls.obj
        symbol = mapsymbol.symbol.pk
        cls.post_data = dict(symbol=symbol, fill_color=faker.color(),
                             stroke_color=faker.color())
        cls.put_data = dict(symbol=symbol, fill_color=faker.color(),
                             stroke_color=faker.color())
        cls.patch_data = dict(symbol=symbol, stroke_color=faker.color())

    def test_is_logged_in(self):
        """test for permission rights, logged_in user has only permission to read"""

        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.assert_http_302_found or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    def test_can_edit_basedata(self):
        """test for permission rights, user who can_edit_basedata has write permission """

        profile = self.profile

        original_permission = profile.can_edit_basedata

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.save()
        self.test_post()

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_201(msg=response.content)

        profile.can_create_process = original_permission
        profile.save()


class TestLayerGroupAPI(_TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "layergroups"
    factory = LayerGroupFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        existing_order = cls.obj.order
        cls.orders = iter(range(existing_order + 1, 100000))

        #order = factory.Sequence(lambda n: faker.pyint(min_value=existing_order,
                                                       #max_value=10))
        cls.post_data = dict(name='posttestname', order=next(cls.orders))
        cls.put_data = dict(name='puttestname', order=next(cls.orders))
        cls.patch_data = dict(name='patchtestname', order=next(cls.orders))

    def test_is_logged_in(self):
        """test for permission rights, logged_in user has only permission to read"""

        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.assert_http_401_unauthorized(response, msg=response.content) #or self.assert_http_302_found(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    #@classmethod
    #def tearDownClass(cls):
        #cls.obj.delete()
        #del cls.obj
        #super().tearDownClass()

    def test_can_edit_basedata(self):
        """test for permission rights, user who can_edit_basedata has write permission """

        profile = self.profile

        original_permission = profile.can_edit_basedata

        # Testprofile, with permission to edit basedata (True)
        profile.can_edit_basedata = True
        profile.save()
        self.test_post()

        # Testprofile, without permission to edit basedata (False)
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        post_data = self.post_data
        post_data['order']=next(self.orders)
        response = self.post(url, **self.url_pks, data=post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_permission
        profile.save()


class TestWMSLayerAPI(_TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "wmslayers"
    factory = WMSLayerFactory


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        wmslayer: WMSLayer = cls.obj
        group = wmslayer.group.pk
        data = dict(url=faker.url(), name=faker.word(), layer_name=faker.word(),
                    order=faker.random_int(), group=group)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_is_logged_in(self):
        """test for permission rights, logged_in user has only permission to read"""

        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.assert_http_302_found or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()


class TestInternalWFSLayerAPI(_TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "internalwfslayers"
    factory = InternalWFSLayerFactory


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        internalwfslayer: InternalWFSLayer = cls.obj
        group = internalwfslayer.group.pk
        internalwfslayer: InternalWFSLayer = cls.obj
        symbol = internalwfslayer.symbol.pk

        data = dict(symbol=symbol, name=faker.word(), layer_name=faker.word(),
                    order=faker.random_int(), group=group)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestSourceAPI(_TestAPI, BasicModelTest, APITestCase):
    """api test Layer"""
    url_key = "sources"
    factory = SourceFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        data = dict(source_type=faker.random_element(SourceTypes),
                date=faker.date(), id_field=faker.uuid4(), url=faker.url(),
                layer=faker.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestAreaLevelAPI(_TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "arealevels"
    factory = AreaLevelFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        area_level: AreaLevel = cls.obj
        source = area_level.source.pk
        layer = area_level.layer.pk

        data = dict(name=faker.word(), order=faker.random_int(),
                    source=source, layer=layer)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestAreaAPI(_TestAPI, BasicModelTest, APITestCase):
    """test if view and serializer are working correctly"""
    url_key = "areas"
    factory = AreaFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        geojson_putpatch = geojson.copy()
        geojson_putpatch['id'] = area.id

        cls.put_data = geojson_putpatch
        cls.patch_data = geojson_putpatch



