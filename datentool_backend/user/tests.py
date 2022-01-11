from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon
from collections import OrderedDict

from datentool_backend.api_test import (BasicModelTest)
from datentool_backend.area.tests import _TestAPI

from .factories import (ProfileFactory, UserFactory, User,
                        PlanningProcessFactory, ScenarioFactory)
from .models import PlanningProcess, Scenario

from faker import Faker
faker = Faker('de-DE')


class PostOnlyWithCanCreateProcessTest:  # ToDo test get, if user is not owner
    """Permission test for PlanningProcessViewSet"""

    def test_delete(self):
        """Test delete with and without can_create_process"""
        self.profile.can_create_process = True
        self.profile.save()
        self._test_delete_forbidden()
        self.profile.can_create_process = False
        self.profile.save()
        self._test_delete_forbidden()

    def test_post(self):
        """Test post with and without can_edit_basedata permissions"""
        self.profile.can_create_process = True
        self.profile.save()
        self._test_post()
        self.profile.can_create_process = False
        self.profile.save()
        self._test_post_forbidden()

    def test_put_patch(self):
        """Test post with and without can_edit_basedata permissions"""
        self.profile.can_create_process = True
        self.profile.save()
        self._test_put_patch_forbidden()
        self.profile.can_create_process = False
        self.profile.save()
        self._test_put_patch_forbidden()

    def test_is_logged_in(self):
        """Test read, if user is authenticated"""
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)

        self.test_list()
        self.test_detail()

    def test_user_not_owner(self):
        """Test, no post permission if user is not owner"""
        # Request user profile is the owner and profile can_create_process
        self.profile.can_create_process = True
        self.profile.save()

        self.patch_data['owner'] = self.obj.owner.pk
        self.patch_data['owner'] = self.obj.owner.pk
        self.post_data['owner'] = self.obj.owner.pk

        self._test_delete_forbidden()
        super()._test_put_patch_forbidden()
        super()._test_post()

        # test_get
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        response = self.get(url, **kwargs)
        self.response_200(msg=response.content)

         # Request user profile is not the owner and profile can_create_process
        self.put_data['owner'] = self.obj3.owner.pk
        self.patch_data['owner'] = self.obj3.owner.pk
        self.post_data['owner'] = self.obj3.owner.pk

        self._test_delete_forbidden()
        super()._test_put_patch_forbidden()
        super()._test_post_forbidden()
        # test_get
        #url = self.url_key + '-detail'
        #kwargs = self.kwargs
        #response = self.get(url, **kwargs)
        # self.response_403(msg=response.content)



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


class TestPlanningProcessAPI(PostOnlyWithCanCreateProcessTest,
                             _TestAPI, BasicModelTest, APITestCase):
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


#class EditScenarioPermissionTest:
    #"""Permission test for ScenarioViewSet"""
    #def test_permission(self):
        #planning_process = self.obj.planning_process
        #original_allow_shared_change = planning_process.allow_shared_change

        ## User is not owner
        #self.put_data['owner'] = 1
        #self.patch_data['owner'] = 1
        #self.post_data['owner'] = 1

        ## allow_shared_change is True, User in Users is True
        #planning_process.allow_shared_change = True
        #self.put_data['user'] = self.obj.users[1]
        #self.patch_data['user'] = self.obj.users[1]
        #self.post_data['user'] = self.obj.users[1]

        #super()._test_put_patch()
        #super()._test_post()


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



        # planning_process.users.add(request.user.profile)
        #user_in_users = request.user.profile in planning_process.users.all()


        # self.obj.planning_process.users.add(request.user.profile)
        ##user_in_users = request.user.profile in obj.planning_process.users.all()
        # user_in_users

    # def test_delete(self):
        #"""Test delete with and without allow_shared_change"""
        #self.profile.allow_shared_change = True
        # self.profile.save()
        # self._test_delete_forbidden()
        #self.profile.allow_shared_change = False
        # self.profile.save()
        # self._test_delete_forbidden()

    # def test_post(self):
        #"""Test post with and without allow_shared_change permissions"""
        #self.profile.allow_shared_change = True
        # self.profile.save()
        # self._test_post()
        #self.profile.allow_shared_change = False
        # self.profile.save()
        # self._test_post_forbidden()

    # def test_put_patch(self):
        #"""Test post with and without allow_shared_change permissions"""
        #self.profile.allow_shared_change = True
        # self.profile.save()
        # self._test_put_patch_forbidden()
        #self.profile.allow_shared_change = False
        # self.profile.save()
        # self._test_put_patch_forbidden()

    # def test_is_logged_in(self):
        #"""Test read, if user is authenticated"""
        # self.client.logout()
        #response = self.get(self.url_key + '-list')
        #self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        # self.client.force_login(user=self.profile.user)

        # self.test_list()
        # self.test_detail()

    # def test_user_not_owner(self):
        # """# Request user profile is/not the owner;
        # allow_shared_change is False -> first statement shall be tested,
        # second has to be false"""
        # Request user profile is the owner
        #self.profile.allow_shared_change = False
        # self.profile.save()

        #self.patch_data['owner'] = self.obj.owner.pk
        #self.patch_data['owner'] = self.obj.owner.pk
        #self.post_data['owner'] = self.obj.owner.pk

        # self._test_delete()
        # super()._test_put_patch()
        # super()._test_post()

        # test_get
        #url = self.url_key + '-detail'
        #kwargs = self.kwargs
        #response = self.get(url, **kwargs)
        # self.response_200(msg=response.content)

         # Request user profile is not the owner
        #self.put_data['owner'] = self.obj3.owner.pk
        #self.patch_data['owner'] = self.obj3.owner.pk
        #self.post_data['owner'] = self.obj3.owner.pk

        # self._test_delete_forbidden()
        # super()._test_put_patch_forbidden()
        # super()._test_post_forbidden()
        # test_get
        #url = self.url_key + '-detail'
        #kwargs = self.kwargs
        #response = self.get(url, **kwargs)
        # self.response_403(msg=response.content)


    # def test_scenario_permission(self):
        # original data
        #planning_process = cls.obj.planning_process

        #original_process_owner = planning_process.owner
        #original_process_users = planning_process.users.all()
        #original_allow_shared_change = planning_process.allow_shared_change

        # self.client.logout()
        #planning_process = self.obj.planning_process
        # self.client.force_login(user=planning_process.owner.user)

        # Testprofile, with permission to edit scenarios
        #request.user.profile = planning_process.owner
        #planning_process.allow_shared_change = True
        # planning_process.save()
