from django.test import TestCase
from .factories import (ProfileFactory, UserFactory, User)


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
