from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelReadTest
from datentool_backend.area.tests import _TestAPI

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


class TestCapacityUploadLogAPI(_TestAPI, BasicModelReadTest, APITestCase):
    """"""
    url_key = "capacityuploadlogs"
    factory = CapacityUploadLogFactory


class TestPlaceUploadLogAPI(_TestAPI, BasicModelReadTest, APITestCase):
    """"""
    url_key = "placeuploadlogs"
    factory = PlaceUploadLogFactory


class TestAreaUploadLogAPI(_TestAPI, BasicModelReadTest, APITestCase):
    """"""
    url_key = "areauploadlogs"
    factory = AreaUploadLogFactory

