from unittest import skip
from django.test import TestCase
from test_plus import APITestCase
from typing import List, Set

from datentool_backend.api_test import (BasicModelTest, LoginTestCase,
                                        WriteOnlyWithAdminAccessTest)
from datentool_backend.area.tests import _TestAPI

from .factories import (ProfileFactory, User, UserFactory,
                        PlanningProcessFactory, ScenarioFactory)
from .models import PlanningProcess, Scenario, Profile

from faker import Faker
faker = Faker('de-DE')


class PostOnlyWithCanCreateProcessTest:  # ToDo test get, if user is not owner
    """Permission test for PlanningProcessViewSet"""

    def test_delete(self):
        """Test delete with and without can_create_process"""
        self.profile.can_create_process = False
        self.profile.save()
        self._test_delete_forbidden()
        self.profile.can_create_process = True
        self.profile.save()
        self._test_delete()

    def test_post(self):
        """Test post with and without can_edit_basedata permissions"""
        self.profile.can_create_process = False
        self.profile.save()
        self._test_post_forbidden()
        self.profile.can_create_process = True
        self.profile.save()
        self._test_post()

    def test_put_patch(self):
        """Test put/patch with and without can_edit_basedata permissions"""
        self.profile.can_create_process = False
        self.profile.save()
        self._test_put_patch_forbidden()
        self.profile.can_create_process = True
        self.profile.save()
        self._test_put_patch()

    def test_is_logged_in(self):
        """Test read, if user is authenticated"""
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(
            response, msg=response.content)

        self.client.force_login(user=self.profile.user)

        self.test_list()
        self.test_detail()

    def test_user_not_owner_post(self):
        """Test, no post permission if user is not owner"""
        # Request user profile is the owner and profile can_create_process
        self.profile.can_create_process = True
        self.profile.save()
        profile2 = ProfileFactory(can_create_process=True)

        self.post_data['owner'] = self.obj.owner.pk
        self._test_post()

        self.post_data['owner'] = profile2.pk
        self._test_post_forbidden()

    def test_user_not_owner_putpatch(self):
        """Test, no put/patch permission if user is not owner"""
        # Request user profile is the owner and profile can_create_process
        self.profile.can_create_process = True
        self.profile.save()
        profile2 = ProfileFactory(can_create_process=True)

        self.client.logout()
        self.client.force_login(user=profile2.user)
        self._test_post_forbidden()
        self.client.logout()

        self.client.force_login(user=self.profile.user)
        self._test_put_patch()

    def test_user_not_owner_delete(self):
        """Test, no delete permission if user is not owner"""
        # Request user profile is the owner and profile can_create_process
        planning_process = self.obj
        self.profile.can_create_process = True
        self.profile.save()

        # create a second user who can create processes
        profile2 = ProfileFactory(can_create_process=True)
        # add him to the users of the planning_process
        # (otherwise) the process is not visible
        planning_process.users.add(profile2)

        # login as profile2
        self.client.logout()
        self.client.force_login(user=profile2.user)
        # this should be forbidden, because profile2 is in
        # planning_process.users, but not the owner
        self._test_delete_forbidden()
        self.client.logout()

        # this should word, because profile2 is in
        # planning_process.users, but not the owner
        self.client.force_login(user=self.profile.user)
        self.test_delete()

    def test_user_not_owner_or_in_users_get(self):
        """Test, no get permission if user is not owner or in users"""

        def _test_get_list_and_detail(self,
                                      current_profile: Profile,
                                      all_pp_ids: Set[int]):

            def get_owner_or_user_ids(profile: Profile) -> List[int]:
                owner = profile.planningprocess_set.all()
                users = profile.shared_with_users.all()
                owner_or_user = (owner | users).distinct()
                return owner_or_user.values_list('id', flat=True)

            # test_get list
            url = self.url_key + '-list'
            url_detail = self.url_key + '-detail'

            self.client.force_login(user=current_profile.user)
            # List view
            response = self.get(url)
            self.response_200(msg=response.content)
            # the ids of the visible planning processes
            response_ids = [p['id'] for p in response.data]
            #  the planning_process-ids where the user is owner or in users
            pp_ids = get_owner_or_user_ids(current_profile)
            #  compare
            self.assertQuerysetEqual(pp_ids, response_ids, ordered=False)
            #  check if detail-view for all visible planning_processes work
            for pp_id in pp_ids:
                response = self.get(url_detail, pk=pp_id)
                self.response_200(msg=response.content)
            #  check if detail-view for all non-visible planning_processes fail
            for pp_id in all_pp_ids - set(pp_ids):
                response = self.get(url_detail, pk=pp_id)
                self.response_404(msg=response.content)
            self.client.logout()

        self.client.logout()
        # create more profiles
        profile1 = self.profile
        profile2 = ProfileFactory(can_create_process=False, admin_access=False)
        profile3 = ProfileFactory(can_create_process=False, admin_access=False)
        profile4 = ProfileFactory(can_create_process=False, admin_access=False)

        #  assign the profiles to some new planning processes
        pp1 = PlanningProcessFactory(owner=profile1)
        pp1.users.set([profile1, profile3])
        pp2 = PlanningProcessFactory(owner=profile1)
        pp2.users.set([profile2, profile3])
        pp3 = PlanningProcessFactory(owner=profile1)
        pp1.users.set([profile3])

        # get all planning professes
        all_pp_ids = set(
            PlanningProcess.objects.all().values_list('id', flat=True))

        #  check the permissions for each profile
        for profile in [profile1, profile2, profile3, profile4]:
            _test_get_list_and_detail(self, profile, all_pp_ids)

        self.client.force_login(user=self.profile.user)


class TestProfile(TestCase):

    def test_profile_factory(self):
        profile = ProfileFactory()
        str(profile)
        self.assertTrue(profile.pk)
        self.assertTrue(profile.user.pk)

    def test_planningprocess_factory(self):
        planning_process = PlanningProcessFactory()
        profile = planning_process.owner
        self.assertTrue(profile.pk)
        self.assertTrue(profile.user.pk)

        scenario = ScenarioFactory()
        planning_process = scenario.planning_process
        profile = planning_process.owner
        self.assertTrue(profile.pk)
        self.assertTrue(profile.user.pk)

    def test_user(self):
        user2 = User.objects.create(username='Test')
        self.assertTrue(user2.profile.pk)

        user2.profile.can_edit_basedata = True
        user2.save()

        profile2 = Profile.objects.get(user=user2)
        self.assertTrue(profile2.can_edit_basedata)


class TestUserAPI(WriteOnlyWithAdminAccessTest,
                  _TestAPI, BasicModelTest, APITestCase):
    """Test user view"""
    url_key = "users"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.admin_access = True
        cls.profile.save()

        cls.obj = ProfileFactory().user

        cls.post_data = {'username': 'NewUser',
                         'password': 'Secret',
                         'profile': {'can_create_process': True,},}


        cls.put_data = {'username': 'RenamedUser',
                         'password': 'Other',
                         'profile': {'can_edit_basedata': True,},}

        cls.patch_data = {'username': 'changed',
                         'profile': {'admin_access': False,
                                     'can_edit_basedata': False,},}


class TestPlanningProcessAPI(PostOnlyWithCanCreateProcessTest,
                             _TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "planningprocesses"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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
                    allow_shared_change=faker.pybool())

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


class TestPlanningProcessProtectCascade(_TestAPI, LoginTestCase, APITestCase):
    url_key = "planningprocesses"

    def test_protection_of_referenced_objects(self):
        """
        Test if the deletion of an object fails, if there are related objects
        using on_delete=PROTECT_CASCADE and we use use_protection=True
        """
        self.profile.can_create_process = True
        self.profile.save()
        planning_process = PlanningProcessFactory(owner=self.profile)
        scenario = ScenarioFactory(planning_process=planning_process)
        kwargs = dict(pk=planning_process.pk)
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)

        response = self.delete(url, **kwargs)
        self.response_403(msg=response.content)
        scenario.delete()
        response = self.delete(url, **kwargs)
        self.response_204(msg=response.content)

    def test_without_protection_of_referenced_objects(self):
        """
        Test if the deletion of an object works, if there are related objects
        using on_delete=PROTECT_CASCADE and we use use_protection=False
        """
        self.profile.can_create_process = True
        self.profile.save()
        planning_process = PlanningProcessFactory(owner=self.profile)
        scenario = ScenarioFactory(planning_process=planning_process)
        kwargs = dict(pk=planning_process.pk)
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)

        #  with override_protection=False it should fail
        response = self.delete(url, data=dict(override_protection=False), **kwargs)
        self.response_403(msg=response.content)

        #  with override_protection=True it should work
        response = self.delete(url, data=dict(override_protection=True), **kwargs)
        self.response_204(msg=response.content)
        #  assert that the referenced scenario is deleted
        self.assertEqual(Scenario.objects.count(), 0)


class EditScenarioPermissionTest:
    """Permission test for ScenarioViewSet"""


class TestScenarioAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "scenarios"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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

    def test_user_in_users(self):
        first_profile = self.profile
        other_profile = ProfileFactory()
        scenario1: Scenario = self.obj

        scenario2 = ScenarioFactory(planning_process__owner=other_profile,
                                    planning_process__allow_shared_change=True)
        scenario3 = ScenarioFactory(planning_process__owner=other_profile,
                                    planning_process__allow_shared_change=False)

        scenario4 = ScenarioFactory(planning_process__owner=other_profile,
                                    planning_process__allow_shared_change=True)
        scenario5 = ScenarioFactory(planning_process__owner=other_profile,
                                    planning_process__allow_shared_change=False)

        scenario4.planning_process.users.add(first_profile)
        scenario4.planning_process.save()

        scenario5.planning_process.users.add(first_profile)
        scenario5.planning_process.save()

        # get
        url = self.url_key + '-list'
        response = self.get(url)
        self.response_200(msg=response.content)
        # result should be only Scenario1 (user is owner)
        # and 4 and 5 (user is in planningprocess.users)
        self.assertSetEqual({s['id'] for s in response.data},
                            {scenario1.id, scenario4.id, scenario5.id})

        # should be able to change only Scenario1 and 4
        self.patch_data['name'] = 'NewName'
        url = self.url_key + '-detail'
        formatjson = dict(format='json')

        # should be able to change only Scenario1 (user is owner)
        # and 4 (user is in planningprocess.users
        # and planningprocess.allow_shared_change=True)
        for scenario in [scenario1, scenario4]:
            response = self.put(url, pk=scenario.pk,
                                data=self.patch_data, extra=formatjson)
            self.response_200(msg=response.content)

        # user should not be able to edit Scenarios 5
        response = self.patch(url, pk=scenario5.pk,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

        # user should not be able to create new scenarios
        # with the planningprocess of Scenarios 2, 3 and 5
        for scenario in [scenario2, scenario3, scenario5]:
            response = self.post(self.url_key + '-list', data=dict(
                name=faker.word(),
                planning_process=scenario.planning_process.pk),
                extra=formatjson)
            self.response_403(msg=response.content)

        # user should be able to create new scenario where he in pp.users and
        # pp.allow_shared_change=True
        response = self.post(self.url_key + '-list', data=dict(
            name=faker.word(),
            planning_process=scenario4.planning_process.pk),
            extra=formatjson)
        self.response_201(msg=response.content)

