from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon

from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI

from .factories import (ProfileFactory, UserFactory, User, ProjectFactory,
                        ScenarioFactory)
from .models import Project, Scenario

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


#class TestProjectAPI(_TestAPI, BasicModelTest, APITestCase):
    #""""""
    #url_key = "projects"
    #factory = ProjectFactory

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()
        #project: Project = cls.obj
        #owner = project.owner.pk
        #users = list(project.users.all().values_list(flat=True))

        #data = dict(name=faker.word(), owner=owner, users=users,
                    #allow_shared_change=faker.pybool(),
                    #map_section=Polygon(((faker.pyint(), faker.pyint()),
                                         #(faker.pyint(), faker.pyint()),
                                         #(faker.pyint(), faker.pyint()))))
        #cls.post_data = data
        #cls.put_data = data
        #cls.patch_data = data


#class TestScenarioAPI(_TestAPI, BasicModelTest, APITestCase):
    #""""""
    #url_key = "scenarios"
    #factory = ScenarioFactory

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()
        #scenario: Scenario = cls.obj
        #project = scenario.project.pk

        #cls.post_data = dict(name=faker.word(), project=project)
        #cls.put_data = dict(name=faker.word(), project=project)
        #cls.patch_data = dict(name=faker.word(), project=project)