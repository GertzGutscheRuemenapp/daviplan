from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest


from .factories import (SymbolFormFactory, MapSymbolsFactory,
                        WMSLayerFactory, InternalWFSLayerFactory,
                        AreaFactory, SourceFactory, LayerGroupFactory)

from faker import Faker

faker = Faker('de-DE')


class TestAreas(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.wfs_layer = WMSLayerFactory()
        cls.layer = InternalWFSLayerFactory()
        cls.source = SourceFactory()
        cls.area = AreaFactory()

    def test_area(self):
        area = self.area


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
    """"""
    url_key = "symbolform"
    factory = SymbolFormFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_data = dict(name='posttestname')
        cls.put_data = dict(name='puttestname')
        cls.patch_data = dict(name='patchtestname')


class TestMapSymbolsAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "mapsymbols"
    factory = MapSymbolsFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        symbol = cls.obj.symbol.pk
        cls.post_data = dict(symbol=symbol, fill_color=faker.color(),
                             stroke_color=faker.color())
        cls.put_data = dict(symbol=symbol, fill_color=faker.color(),
                             stroke_color=faker.color())
        cls.patch_data = dict(symbol=symbol, stroke_color=faker.color())


""" Test for LayerGroup is not working!
class TestLayerGroupAPI(_TestAPI, BasicModelTest, APITestCase):

    url_key = "layergroup"
    factory = LayerGroupFactory


         @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_data = dict(name='posttestname')
        cls.put_data = dict(name='puttestname')
        cls.patch_data = dict(name='patchtestname')


# Test for WMSLayer, InternalWFSLayer, Source
is test for WMSLayer, InternalWFSLayer, Source necessary? already in class TestAreas


# Test for Area Level and Area -> same question, already in class TestAreas?

   """
