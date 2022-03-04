from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest)
from datentool_backend.area.tests import TestAPIMixin, TestPermissionsMixin

from faker import Faker

faker = Faker('de-DE')


from .factories import (ModeFactory,
                        ModeVariantFactory,
                        CutOffTimeFactory,
                        )
from .models import ModeVariant


class TestModeModels(TestCase):

    def test_mode_variant(self):
        mode_variant = ModeVariantFactory()

    def test_cut_off_time(self):
        cut_off_time = CutOffTimeFactory()


class TestModeVariantAPI(WriteOnlyWithCanEditBaseDataTest,
                         TestPermissionsMixin,
                         TestAPIMixin,
                         BasicModelTest,
                         APITestCase):
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
