from django.test import TestCase
from .factories import (WMSLayerFactory, InternalWFSLayerFactory,
                        AreaFactory, SourceFactory)


class TestAreas(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.wfs_layer = WMSLayerFactory()
        cls.layer = InternalWFSLayerFactory()
        cls.source = SourceFactory()
        cls.area = AreaFactory()

    def test_area(self):
         area = self.area