from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon
from collections import OrderedDict

from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI, _TestPermissions

from .factories import (ProfileFactory, UserFactory, User,
                        PlanningProcessFactory, ScenarioFactory)
from .models import PlanningProcess, Scenario

from faker import Faker
faker = Faker('de-DE')


class TestProfile(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.profile = ProfileFactory()

    def test_profile(self):
        profile = self.profile

    def test_user(self):
        user = UserFactory()
        self.assertTrue(user.profile)
        user.profile.admin_access = False
        user.save()

        user2 = User.objects.create(username='Test')
        self.assertTrue(user2.profile.pk)


class TestPlanningProcessAPI(_TestAPI, BasicModelTest, APITestCase):  # test, if user is none and if user is not owner are missing
    """"""
    url_key = "planningprocesses"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user2 = ProfileFactory()  # second user to extend test_project_creation_permission
        cls.user3 = ProfileFactory()  # third user to extend test_project_creation_permission

        # assign user profiles to planningprocesses, to test permission rights
        cls.obj = PlanningProcessFactory(owner=cls.profile)
        cls.obj2 = PlanningProcessFactory(owner=cls.profile)
        cls.obj3 = PlanningProcessFactory(owner=cls.user2)


        planningprocess: PlanningProcess = cls.obj
        owner = planningprocess.owner.pk
        users = list(planningprocess.users.all().values_list(flat=True))

        data = dict(owner=owner,
                    users=users,
                    name=faker.word(),
                    allow_shared_change= faker.pybool())

        cls.post_data = data
        data_putpatch = data.copy()
        data_putpatch['id'] = planningprocess.id
        cls.put_data = data_putpatch
        cls.patch_data = data_putpatch

    @classmethod
    def tearDownClass(cls):
        cls.obj.delete()
        cls.obj2.delete()
        cls.obj3.delete()
        del cls.obj
        del cls.obj2
        del cls.obj3
        super().tearDownClass()

    def test_process_creation_permission(self):
        """Test the process creation permission of the profile"""
        profile = self.profile

        original_permission = profile.can_create_process

        # Testprofile, with permission to create project (True)
        profile.can_create_process = True
        profile.save()
        self.test_post()

        # Testprofile, without permission to create project (False)
        profile.can_create_process = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_create_process = original_permission
        profile.save()


class TestScenarioAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "scenarios"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.obj = ScenarioFactory(planning_process__owner=cls.profile)

        scenario: Scenario = cls.obj
        planning_process = scenario.planning_process.pk

        cls.post_data = dict(name=faker.word(), planning_process=planning_process)
        cls.put_data = dict(name=faker.word(), planning_process=planning_process)
        cls.patch_data = dict(name=faker.word(), planning_process=planning_process)

    @classmethod
    def tearDownClass(cls):
        planning_process = cls.obj.planning_process
        cls.obj.delete()
        del cls.obj
        planning_process.delete()
        super().tearDownClass()


    def test_is_logged_in(self):
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    def test_scenario_permission(self):
        self.client.logout()
        planning_process = self.obj.planning_process
        self.client.force_login(user=planning_process.owner.user)

        original_process_owner = planning_process.owner
        original_allow_shared_change = planning_process.allow_shared_change

        # Testprofile, with permission to edit scenarios
        #self.request.user.profile = planning_process.owner
        planning_process.allow_shared_change = True
        planning_process.save()

        self.test_post()

        ## Testprofile, without permission to edit scenarios

        ## post
        #response = self.post(url, **self.url_pks, data=self.post_data,
                             #extra={'format': 'json'})
        #self.response_403(msg=response.content)


