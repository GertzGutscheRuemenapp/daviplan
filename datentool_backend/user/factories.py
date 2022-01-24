import factory
from factory.django import DjangoModelFactory, mute_signals
from faker import Faker

from .models import (User,
                     Profile,
                     post_save,
                     Year,
                     PlanningProcess,
                     Infrastructure,
                     Service,
                     )

from datentool_backend.area.factories import MapSymbolFactory

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


class YearFactory(DjangoModelFactory):
    class Meta:
        model = Year

    year = faker.unique.year()


class PlanningProcessFactory(DjangoModelFactory):
    class Meta:
        model = PlanningProcess

    owner = factory.SubFactory(ProfileFactory)
    name = faker.word()
    allow_shared_change = faker.pybool()


class InfrastructureFactory(DjangoModelFactory):
    class Meta:
        model = Infrastructure
    name = faker.word()
    description = faker.sentence()
    # sensitive_data
    symbol = factory.SubFactory(MapSymbolFactory)
    order = faker.unique.pyint(max_value=10)

    @factory.post_generation
    def editable_by(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of profiles were passed in, use them
            for profile in extracted:
                self.editable_by.add(profile)
        else:
            profile = Profile.objects.first()
            if profile is not None:
                self.editable_by.add(profile)

    @factory.post_generation
    def accessible_by(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of profiles were passed in, use them
            for profile in extracted:
                self.accessible_by.add(profile)
        else:
            profile = Profile.objects.first()
            if profile is not None:
                self.accessible_by.add(profile)


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = Service

    name = faker.word()
    description = faker.sentence()
    infrastructure = factory.SubFactory(InfrastructureFactory)
    # editable_by
    capacity_singular_unit = faker.word()
    capacity_plural_unit = faker.word()
    has_capacity = True
    demand_singular_unit = faker.word()
    demand_plural_unit = faker.word()
    quota_type = faker.word()
    demand_name = faker.word()
    demand_description = faker.word()

