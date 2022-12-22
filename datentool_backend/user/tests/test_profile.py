from django.test import TestCase
from test_plus import APITestCase

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithAdminAccessTest,
                                        TestAPIMixin,
                                        )

from datentool_backend.user.factories import ProfileFactory
from datentool_backend.user.models import User, Profile


class TestProfile(TestCase):

    def test_profile_factory(self):
        profile = ProfileFactory()
        str(profile)
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
