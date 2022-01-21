from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest)
from datentool_backend.area.tests import TestAPIMixin, TestPermissionsMixin

from faker import Faker

faker = Faker('de-DE')


from .factories import (ModeFactory,
                        ModeVariantFactory,
                        RouterFactory,
                        IndicatorFactory,
                        CutOffTimeFactory,
                        # MatrixCellStopFactory,
                        # ReachabilityMatrixFactory,
                        )
from .models import (ModeVariant,
                     # CutOffTime,
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

    def test_cut_off_time(self):
        cut_off_time = CutOffTimeFactory()

    #def test_matrix_cell_stop(self):
        #matrix_cell_stop = MatrixCellStopFactory()



class TestModeAPI(WriteOnlyWithCanEditBaseDataTest,
                  TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "modes"
    factory = ModeFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.post_data = data = dict(name=faker.word())
        cls.put_data = data = dict(name=faker.word())
        cls.patch_data = data = dict(name=faker.word())


class TestModeVariantAPI(WriteOnlyWithCanEditBaseDataTest,
                         TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "modevariants"
    factory = ModeVariantFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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
    # def setUpTestData(cls):
        # super().setUpTestData()
        #reachabilitymatrix: ReachabilityMatrix = cls.obj
        #from_cell = reachabilitymatrix.from_cell.pk
        #to_cell = reachabilitymatrix.to_cell.pk
        #variant = reachabilitymatrix.variant.pk

        #data = dict(from_cell=from_cell, to_cell=to_cell, variant=variant,
                    #minutes=faker.pyfloat(positive=True))
        #cls.post_data = data
        #cls.put_data = data
        #cls.patch_data = data


class TestRouterAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "routers"
    factory = RouterFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(name = faker.word(), osm_file = faker.file_path(),
                    tiff_file = faker.file_path(), gtfs_file = faker.file_path(),
                    build_date = faker.date(),
                    buffer = faker.random_number(digits=2))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestIndicatorAPI(WriteOnlyWithCanEditBaseDataTest,
                       TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "indicators"
    factory = IndicatorFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        indicator: Indicator = cls.obj
        service = indicator.service.pk

        data = dict(indicator_type = faker.random_element(IndicatorTypes),
                    name = faker.word(), parameters = faker.json(),
                    service = service)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
