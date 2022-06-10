from factory.django import DjangoModelFactory

from .models import (Mode, ModeVariant, CutOffTime, Network)
from datentool_backend.infrastructure.factories import InfrastructureFactory

import factory
from faker import Faker
faker = Faker('de-DE')


class NetworkFactory(DjangoModelFactory):
    class Meta:
        model = Network
    name = faker.word()


class ModeVariantFactory(DjangoModelFactory):
    class Meta:
        model = ModeVariant
    network = factory.SubFactory(NetworkFactory)
    mode = factory.Faker(
        'random_element', elements=[x[0] for x in Mode.choices])


class CutOffTimeFactory(DjangoModelFactory):
    class Meta:
        model = CutOffTime
    mode_variant = factory.SubFactory(ModeVariantFactory)
    infrastructure = factory.SubFactory(InfrastructureFactory)
    minutes = faker.pyfloat()
