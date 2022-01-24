from django.test import TestCase
from test_plus import APITestCase
from unittest import skip


from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        WriteOnlyWithAdminAccessTest,
                                        )
from datentool_backend.area.tests import TestAPIMixin, TestPermissionsMixin

from .factories import (AgeGroupFactory,
                        GenderFactory,
                        DemandRateSetFactory,
                        DemandRateFactory,
                        )
from .models import (DemandRate, DemandRateSet)
from .constants import RegStatAgeGroup, RegStatAgeGroups

from faker import Faker
faker = Faker('de-DE')


class TestGenderAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "gender"
    factory = GenderFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.post_data = dict(name=faker.word())
        cls.put_data = dict(name=faker.word())
        cls.patch_data = dict(name=faker.word())



class TestAgeGroupAPI(WriteOnlyWithAdminAccessTest,
                      TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "agegroups"
    factory = AgeGroupFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(from_age=faker.pyint(max_value=127),
                    to_age=faker.pyint(max_value=127))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    @skip('only write access with admin access, not with can_edit_basedata')
    def test_can_edit_basedata(self):
        pass

    def test_admin_access(self):
        """write permission if user has admin_access"""
        super().admin_access()

    def test_default_agegroups(self):
        """test default agegroups"""
        response = self.get_check_200(self.url_key + '-list',
                                      data={'defaults': True, })
        assert(len(response.data) == len(RegStatAgeGroups.agegroups))

    def test_check_and_replace_agegroups(self):
        """check the agegroups"""
        # logout to see if check is not allowed
        self.client.logout()
        response = self.post(self.url_key + '-check')
        self.assert_http_401_unauthorized(response)

        # login and check that the current agegroups are not valid
        self.client.force_login(self.profile.user)

        response = self.get_check_200(self.url_key + '-list')
        current_agegroups = response.data

        response = self.post(self.url_key + '-check',
                             data=current_agegroups,
                             extra={'format': 'json'})
        self.assert_http_200_ok(response)
        self.assertEqual(response.data['valid'], False)

        # logout to see if check is not allowed
        self.client.logout()
        response = self.post(self.url_key + '-replace')
        self.assert_http_401_unauthorized(response)

        # login without can_edit_basedata is not allowed
        self.client.force_login(self.profile.user)
        response = self.post(self.url_key + '-replace')
        self.assert_http_403_forbidden(response)

        #  with can_edit_basedata it should work
        self.profile.can_edit_basedata = True
        self.profile.save()

        #  get the default agegroups
        response = self.get_check_200(self.url_key + '-list',
                                      data={'defaults': True, })
        default_agegroups = response.data


        #  post them to the replace route
        response = self.post(self.url_key + '-replace',
                             data=default_agegroups,
                             extra={'format': 'json'})
        self.assert_http_200_ok(response)
        assert(len(response.data) == len(RegStatAgeGroups.agegroups))

        response = self.get_check_200(self.url_key + '-list')
        current_agegroups = response.data

        #  now the check should work
        response = self.post(self.url_key + '-check',
                             data=current_agegroups,
                             extra={'format': 'json'})

        self.assert_http_200_ok(response)
        self.assertEqual(response.data['valid'], True)

        # change some agegroup definition
        pk1 = current_agegroups[-1]['id']
        pk2 = current_agegroups[-2]['id']

        self.profile.admin_access = True
        self.profile.save()
        response = self.patch(self.url_key + '-detail', pk=pk1,
                              data={'fromAge': 83, }, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        response = self.patch(self.url_key + '-detail', pk=pk2,
                              data={'toAge': 82, }, extra={'format': 'json'})
        self.assert_http_200_ok(response)

        #  get the whole agegroups
        response = self.get_check_200(self.url_key + '-list')
        current_agegroups = response.data

        #  check if they are still valid
        response = self.post(self.url_key + '-check',
                             data=current_agegroups,
                             extra={'format': 'json'})

        #  they should fail now
        self.assert_http_200_ok(response)
        self.assertEqual(response.data['valid'], False)


class TestRegStatAgeGroup(TestCase):

    def test_repr_of_agegroups(self):
        """Test the representation of agegroups"""
        ag1 = RegStatAgeGroup(from_age=4, to_age=8)
        str(ag1)
        repr(ag1)

    def test_compare_agegroups(self):
        """Test to compare agegroups"""
        ag1 = RegStatAgeGroup(from_age=4, to_age=8)
        ag2 = RegStatAgeGroup(from_age=9, to_age=12)
        ag3 = RegStatAgeGroup(from_age=9, to_age=12)
        assert ag2 == ag3
        assert ag1 != ag2
        assert ag1 != ag3


class TestDemand(TestCase):
    def test_demand_rate_set(self):
        demand_rate_set = DemandRateSetFactory()
        demand_rate = DemandRateFactory(demand_rate_set=demand_rate_set)
        print(demand_rate)


class TestDemandRateSetAPI(WriteOnlyWithCanEditBaseDataTest,
                           TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "demandratesets"
    factory = DemandRateSetFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        demandrateset: DemandRateSet = cls.obj
        service = demandrateset.service.pk

        data = dict(name=faker.word(), is_default=faker.pybool(), service=service)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestDemandRateAPI(WriteOnlyWithCanEditBaseDataTest,
                        TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "demandrates"
    factory = DemandRateFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        demandrate: DemandRate = cls.obj
        year = demandrate.year.pk
        age_group = demandrate.age_group.pk
        gender = demandrate.gender.pk
        demand_rate_set = demandrate.demand_rate_set.pk

        data = dict(year=year,
                    age_group=age_group,
                    gender=gender,
                    demand_rate_set=demand_rate_set)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
