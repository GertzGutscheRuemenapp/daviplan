from django.test import TestCase
from test_plus import APITestCase

from datentool_backend.api_test import (BasicModelTest,
                                        TestAPIMixin,
                                        LoginTestCase,
                                        )


from datentool_backend.user.factories import (ProfileFactory,
                                              PlanningProcessFactory,
                                              )
from datentool_backend.infrastructure.models import Scenario
from datentool_backend.infrastructure.factories import ScenarioFactory

from faker import Faker
faker = Faker('de-DE')


class TestScenario(TestCase):

    def test_profile_in_sub_factory(self):
        scenario = ScenarioFactory()
        planning_process = scenario.planning_process
        profile = planning_process.owner
        self.assertTrue(profile.pk)
        self.assertTrue(profile.user.pk)


class TestScenarioAPI(TestAPIMixin, BasicModelTest, APITestCase):
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


class TestPlanningProcessProtectCascade(TestAPIMixin, LoginTestCase, APITestCase):
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

