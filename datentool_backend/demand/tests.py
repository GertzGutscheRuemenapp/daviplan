from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI

from .factories import DemandRateSetFactory, DemandRateFactory
from .models import DemandRate

from faker import Faker

faker = Faker('de-DE')


class TestDemand(TestCase):

    def test_demand_rate_set(self):
        demand_rate_set = DemandRateSetFactory()
        demand_rate = DemandRateFactory(demand_rate_set=demand_rate_set)
        print(demand_rate)


class TestDemandRateSetAPI(_TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "demandratesets"
    factory = DemandRateSetFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        data = dict(name=faker.word(), is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_is_logged_in(self):
        """read_only"""

        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    def test_can_edit_basedata(self):
        """ write permission """
        profile = self.profile

        original_permission = profile.can_edit_basedata

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.save()
        self.test_post()

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_permission
        profile.save()

class TestDemandRateAPI(_TestAPI, BasicModelTest, APITestCase):
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

    def test_is_logged_in(self):
        """read_only"""

        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    def test_can_edit_basedata(self):
        """write permission"""
        profile = self.profile

        original_permission = profile.can_edit_basedata

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.save()
        self.test_post()

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_permission
        profile.save()