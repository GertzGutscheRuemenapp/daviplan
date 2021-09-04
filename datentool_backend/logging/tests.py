from django.test import TestCase
from .factories import (CapacityUploadLogFactory,
                        PlaceUploadLogFactory,
                        AreaUploadLogFactory)
from ..user.factories import ProfileFactory


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
