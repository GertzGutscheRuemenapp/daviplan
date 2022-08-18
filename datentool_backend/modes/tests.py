from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin, TestPermissionsMixin)

from faker import Faker

faker = Faker('de-DE')


from .factories import (ModeVariantFactory,
                        CutOffTimeFactory,
                        NetworkFactory
                        )
from .models import ModeVariant, Mode, Network


class TestNetworkModels(TestCase):

    def test_mode_variant(self):
        mode_variant = ModeVariantFactory()

    def test_cut_off_time(self):
        cut_off_time = CutOffTimeFactory()

    def test_mode_default_unique(self):
        network_1 = NetworkFactory()
        network_2 = NetworkFactory()
        network_3 = NetworkFactory()

        network_3.is_default = True
        network_3.save()
        network_2.is_default = True
        network_2.save()

        self.assertEqual(Network.objects.get(is_default=True), network_2)

        network_2.is_default = False
        network_2.save()
        self.assertEqual(len(Network.objects.filter(is_default=True)), 0)


class TestNetworkAPI(WriteOnlyWithCanEditBaseDataTest,
                     TestPermissionsMixin,
                     TestAPIMixin,
                     BasicModelTest,
                     APITestCase):
    """Test to post, put and patch data"""
    url_key = "networks"
    factory = NetworkFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(name=faker.word(),
                    is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
