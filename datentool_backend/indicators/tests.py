from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI, _TestPermissions

from faker import Faker

faker = Faker('de-DE')


from .factories import (ModeFactory, ModeVariantFactory, RouterFactory,
                        IndicatorFactory,
                        #ReachabilityMatrixFactory,
                        )
from .models import (ModeVariant,
                     # ReachabilityMatrix,
                     IndicatorTypes, Indicator)


class TestIndicator(TestCase):

    def test_mode_variant(self):
        mode_variant = ModeVariantFactory()

    def test_router(self):
        router = RouterFactory()

    def test_indicator(self):
        indicator = IndicatorFactory()

    #def test_matrix(self):
        #matrix = ReachabilityMatrixFactory()


class TestModeAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "modes"
    factory = ModeFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_data = data = dict(name=faker.word())
        cls.put_data = data = dict(name=faker.word())
        cls.patch_data = data = dict(name=faker.word())


class TestModeVariantAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "modevariants"
    factory = ModeVariantFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        modevariant: ModeVariant = cls.obj
        mode = modevariant.mode.pk

        data = dict(mode=mode, name=faker.word(),
                    meta=faker.json(),
                    is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


#class TestReachabilityMatrixAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    #"""Test to post, put and patch data"""
    #url_key = "reachabilitymatrices"
    #factory = ReachabilityMatrixFactory

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()
        #reachabilitymatrix: ReachabilityMatrix = cls.obj
        #from_cell = reachabilitymatrix.from_cell.pk
        #to_cell = reachabilitymatrix.to_cell.pk
        #variant = reachabilitymatrix.variant.pk

        #data = dict(from_cell=from_cell, to_cell=to_cell, variant=variant,
                    #minutes=faker.pyfloat(positive=True))
        #cls.post_data = data
        #cls.put_data = data
        #cls.patch_data = data


class TestRouterAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "routers"
    factory = RouterFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        data = dict(name = faker.word(), osm_file = faker.file_path(),
                    tiff_file = faker.file_path(), gtfs_file = faker.file_path(),
                    build_date = faker.date(),
                    buffer = faker.random_number(digits=2))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestIndicatorAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "indicators"
    factory = IndicatorFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        indicator: Indicator = cls.obj
        service = indicator.service.pk

        data = dict(indicator_type = faker.random_element(IndicatorTypes),
                    name = faker.word(), parameters = faker.json(),
                    service = service)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
