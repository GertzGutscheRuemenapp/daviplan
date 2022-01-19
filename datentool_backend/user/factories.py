import factory
from factory.django import DjangoModelFactory, mute_signals
from faker import Faker

from .models import User, Profile, post_save, PlanningProcess, Scenario


faker = Faker('de-DE')

@mute_signals(post_save)
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: faker.unique.name())
    profile = factory.RelatedFactory('datentool_backend.user.factories.ProfileFactory',
                                     factory_related_name='user')


@mute_signals(post_save)
class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile

    admin_access = faker.pybool()
    can_create_process = faker.pybool()
    can_edit_basedata = faker.pybool()
    user = factory.SubFactory(UserFactory, profile=None)


class PlanningProcessFactory(DjangoModelFactory):
    class Meta:
        model = PlanningProcess

    owner = factory.SubFactory(ProfileFactory)
    name = faker.word()
    allow_shared_change = faker.pybool()


class ScenarioFactory(DjangoModelFactory):
    class Meta:
        model = Scenario

    name = faker.word()
    planning_process = factory.SubFactory(PlanningProcessFactory)
