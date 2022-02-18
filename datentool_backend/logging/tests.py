from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelReadTest,
                                        ReadOnlyWithAdminBasedataAccessTest)
from datentool_backend.api_test import TestAPIMixin

from .factories import (CapacityUploadLogFactory, PlaceUploadLogFactory,
                        AreaUploadLogFactory)

from ..user.factories import ProfileFactory

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)

from faker import Faker

faker = Faker('de-DE')


class TestLogs(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.profile = ProfileFactory()

    def test_capacity_log(self):
        log = CapacityUploadLogFactory(user=self.profile)

    def test_indicator(self):
        log = PlaceUploadLogFactory(user=self.profile)

    def test_matrix(self):
        log = AreaUploadLogFactory()


class TestCapacityUploadLogAPI(ReadOnlyWithAdminBasedataAccessTest, TestAPIMixin, BasicModelReadTest, APITestCase):
    """"""
    url_key = "capacityuploadlogs"
    factory = CapacityUploadLogFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        capacityuploadlog: CapacityUploadLog = cls.obj
        service = capacityuploadlog.service.pk
        user = capacityuploadlog.user.pk

        data = dict(user=user, date = faker.date(), text = faker.sentence(),
                    service=service)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPlaceUploadLogAPI(ReadOnlyWithAdminBasedataAccessTest, TestAPIMixin, BasicModelReadTest, APITestCase):
    """"""
    url_key = "placeuploadlogs"
    factory = PlaceUploadLogFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        placeuploadlog: PlaceUploadLog = cls.obj
        infrastructure = placeuploadlog.infrastructure.pk
        user = placeuploadlog.user.pk

        data = dict(user=user, date = faker.date(), text = faker.sentence(),
                    infrastructure=infrastructure)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestAreaUploadLogAPI(ReadOnlyWithAdminBasedataAccessTest, TestAPIMixin, BasicModelReadTest, APITestCase):
    """"""
    url_key = "areauploadlogs"
    factory = AreaUploadLogFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        areauploadlog: AreaUploadLog = cls.obj
        level = areauploadlog.level.pk
        user = areauploadlog.user.pk

        data = dict(user=user, date = faker.date(), text = faker.sentence(),
                    level=level)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
