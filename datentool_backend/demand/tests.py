from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI, _TestPermissions

from .factories import DemandRateSetFactory, DemandRateFactory
from .models import DemandRate

from faker import Faker

faker = Faker('de-DE')


class TestDemand(TestCase):
    def test_demand_rate_set(self):
        demand_rate_set = DemandRateSetFactory()
        demand_rate = DemandRateFactory(demand_rate_set=demand_rate_set)
        print(demand_rate)


class TestDemandRateSetAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "demandratesets"
    factory = DemandRateSetFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        demandrateset: DemandRateSet = cls.obj
        service = demandrateset.service.pk

        data = dict(name=faker.word(), is_default=faker.pybool(), service=service)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestDemandRateAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "demandrates"
    factory = DemandRateFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        demandrate: DemandRate = cls.obj
        year = demandrate.year.pk
        age_group = demandrate.age_group.pk
        demand_rate_set = demandrate.demand_rate_set.pk

        data = dict(year=year, age_group=age_group,
                    demand_rate_set=demand_rate_set)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
