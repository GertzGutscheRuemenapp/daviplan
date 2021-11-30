from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon
from collections import OrderedDict

from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI

from .factories import (ProfileFactory, UserFactory, User,
                        ProjectFactory,ScenarioFactory)
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


class TestProjectAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "projects"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.obj = ProjectFactory(owner=cls.profile)

        project: Project = cls.obj
        owner = project.owner.pk
        users = list(project.users.all().values_list(flat=True))
        properties = OrderedDict(owner=owner,
                                 users=users,
                                 name=faker.word(),
                                 allow_shared_change= faker.pybool())
        geojson = {
            'type': 'Feature',
            'geometry': project.map_section.ewkt,
            'properties': properties,
        }

        cls.post_data = geojson
        geojson_putpatch = geojson.copy()
        geojson_putpatch['id'] = project.id
        cls.put_data = geojson_putpatch
        cls.patch_data = geojson_putpatch

    @classmethod
    def tearDownClass(cls):
        cls.obj.delete()
        del cls.obj
        super().tearDownClass()

    def test_project_creation_permission(self):
        """Test the project creation permission of the profile"""
        profile = self.profile

        original_permission = profile.can_create_project

        # Testprofile, with permission to create project (True)
        profile.can_create_project = True
        profile.save()
        self.test_post()

        # Testprofile, without permission to create project (False)
        profile.can_create_project = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_create_project = original_permission
        profile.save()


class TestScenarioAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "scenarios"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.obj = ScenarioFactory(project__owner=cls.profile)

        scenario: Scenario = cls.obj
        project = scenario.project.pk

        cls.post_data = dict(name=faker.word(), project=project)
        cls.put_data = dict(name=faker.word(), project=project)
        cls.patch_data = dict(name=faker.word(), project=project)

    @classmethod
    def tearDownClass(cls):
        project = cls.obj.project
        cls.obj.delete()
        del cls.obj
        project.delete()
        super().tearDownClass()
