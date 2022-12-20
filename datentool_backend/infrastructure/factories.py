from factory.django import DjangoModelFactory

from datentool_backend.user.factories import Profile

from .models import Infrastructure, Service


from datentool_backend.area.factories import MapSymbolFactory

import factory
from faker import Faker
faker = Faker('de-DE')


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
    facility_singular_unit = faker.word()
    facility_article = faker.word()
    facility_plural_unit = faker.word()
    direction_way_relationship = faker.pyint(max_value=2, min_value=1)
