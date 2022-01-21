from factory.django import DjangoModelFactory

from .models import (Mode, ModeVariant, CutOffTime)
from datentool_backend.user.factories import InfrastructureFactory

import factory
from faker import Faker
faker = Faker('de-DE')


class ModeFactory(DjangoModelFactory):
    class Meta:
        model = Mode

    name = factory.Sequence(lambda n: faker.unique.name())


class ModeVariantFactory(DjangoModelFactory):
    class Meta:
        model = ModeVariant

    mode = factory.SubFactory(ModeFactory)
    name = factory.LazyAttribute(lambda o: f'{o.mode.name}_Variant')
    meta = faker.json(num_rows=3, indent=True)
    is_default = faker.pybool()


class CutOffTimeFactory(DjangoModelFactory):
    class Meta:
        model = CutOffTime
    mode_variant = factory.SubFactory(ModeVariantFactory)
    infrastructure = factory.SubFactory(InfrastructureFactory)
    minutes = faker.pyfloat()
