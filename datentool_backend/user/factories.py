import factory
from factory.django import DjangoModelFactory, mute_signals
from faker import Faker
from django.db.models.signals import post_save

from .models import User, Profile

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
