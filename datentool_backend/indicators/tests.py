from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI

from faker import Faker

faker = Faker('de-DE')


from .factories import (ModeVariantFactory, RouterFactory,
                        IndicatorFactory, ReachabilityMatrixFactory)


class TestIndicator(TestCase):

    def test_mode_variant(self):
        mode_variant = ModeVariantFactory()

    def test_router(self):
        router = RouterFactory()

    def test_indicator(self):
        indicator = IndicatorFactory()

    def test_matrix(self):
        matrix = ReachabilityMatrixFactory()


#class TestModeAPI(_TestAPI, BasicModelTest, APITestCase):
    #"""Test to post, put and patch data"""
    #url_key = "modes"
    #factory = ModeFactory

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()
        #capacity: Capacity = cls.obj
        #place = capacity.place.pk
        #service = capacity.service.pk

        #data = dict(place=place, service=service,
                    #capacity=faker.pyfloat(positive=True), from_year=faker.year())
        #cls.post_data = data
        #cls.put_data = data
        #cls.patch_data = data