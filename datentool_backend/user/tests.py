from django.test import TestCase
from .factories import (ProfileFactory)


class TestProfile(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.profile = ProfileFactory()

    def test_profile(self):
         profile = self.profile
