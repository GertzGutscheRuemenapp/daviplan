from factory.django import DjangoModelFactory

from .models import (Mode, ModeVariant, CutOffTime)
from datentool_backend.infrastructure.factories import InfrastructureFactory

import factory
from faker import Faker
faker = Faker('de-DE')


class ModeVariantFactory(DjangoModelFactory):
    class Meta:
        model = ModeVariant

    mode = factory.Faker(
        'random_element', elements=[x[0] for x in Mode.choices])
    name = factory.LazyAttribute(lambda o: f'{Mode(o.mode).label}_Variant')
    meta = faker.json(num_rows=3, indent=True)
    is_default = faker.pybool()


class CutOffTimeFactory(DjangoModelFactory):
    class Meta:
        model = CutOffTime
    mode_variant = factory.SubFactory(ModeVariantFactory)
    infrastructure = factory.SubFactory(InfrastructureFactory)
    minutes = faker.pyfloat()
