from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin, TestPermissionsMixin)

from faker import Faker

faker = Faker('de-DE')


from .factories import (ModeVariantFactory,
                        CutOffTimeFactory,
                        )
from .models import ModeVariant, Mode


class TestModeModels(TestCase):

    def test_mode_variant(self):
        mode_variant = ModeVariantFactory()

    def test_cut_off_time(self):
        cut_off_time = CutOffTimeFactory()

    def test_mode_default_unique(self):
        walk_variant_1 = ModeVariantFactory(mode=Mode.WALK.value)
        walk_variant_2 = ModeVariantFactory(mode=Mode.WALK.value)
        walk_variant_3 = ModeVariantFactory(mode=Mode.WALK.value)
        car_variant_1 = ModeVariantFactory(mode=Mode.CAR.value)
        car_variant_2 = ModeVariantFactory(mode=Mode.CAR.value)
        car_variant_3 = ModeVariantFactory(mode=Mode.CAR.value)

        walk_variant_3.is_default = True
        walk_variant_3.save()
        walk_variant_2.is_default = True
        walk_variant_2.save()

        car_variant_2.is_default = True
        car_variant_2.save()
        car_variant_3.is_default = True
        car_variant_3.save()
        car_variant_1.is_default = False
        car_variant_1.save()

        self.assertEqual(ModeVariant.objects.get(
            is_default=True, mode=Mode.WALK.value), walk_variant_2)
        self.assertEqual(ModeVariant.objects.get(
            is_default=True, mode=Mode.CAR.value), car_variant_3)

        walk_variant_2.is_default = False
        walk_variant_2.save()
        self.assertEqual(len(ModeVariant.objects.filter(
            is_default=True, mode=Mode.WALK.value)), 0)


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
        mode = modevariant.mode

        data = dict(mode=mode, name=faker.word(),
                    meta=faker.json(),
                    is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
