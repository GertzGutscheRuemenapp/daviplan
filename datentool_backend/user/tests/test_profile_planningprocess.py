from typing import List, Set

from django.test import TestCase
from test_plus import APITestCase

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithAdminAccessTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin,
                                        )

from datentool_backend.user.factories import (ProfileFactory,
                                              YearFactory,
                                              PlanningProcessFactory,
                                              )
from datentool_backend.user.models import (User,
                                           Profile,
                                           PlanningProcess,
                                           )

from faker import Faker
faker = Faker('de-DE')


class TestProfile(TestCase):

    def test_profile_factory(self):
        profile = ProfileFactory()
        str(profile)
        self.assertTrue(profile.pk)
        self.assertTrue(profile.user.pk)

    def test_planningprocess_factory(self):
        """Test if user and profile are created in a SubFactory"""
        planning_process = PlanningProcessFactory()
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
                  TestAPIMixin, BasicModelTest, APITestCase):
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


class TestYearAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "years"
    factory = YearFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.post_data = dict(year=1990)
        cls.put_data = dict(year=1995, is_default=False)
        cls.patch_data = dict(year=2000, is_default=True)


class PostOnlyWithCanCreateProcessTest:
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


class TestPlanningProcessAPI(PostOnlyWithCanCreateProcessTest,
                             TestAPIMixin, BasicModelTest, APITestCase):
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

