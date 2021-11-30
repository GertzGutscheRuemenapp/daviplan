from faker import Faker
import factory
from factory.django import DjangoModelFactory
from .models import DemandRateSet, DemandRate
from ..population.factories import (AgeClassificationFactory,
                                    AgeGroupFactory,
                                    YearFactory)

faker = Faker('de-DE')


class DemandRateSetFactory(DjangoModelFactory):
    class Meta:
        model = DemandRateSet
    name = faker.word()
    is_default = faker.pybool()
    age_classification = factory.SubFactory(AgeClassificationFactory)


class DemandRateFactory(DjangoModelFactory):
    class Meta:
        model = DemandRate
    year = factory.SubFactory(YearFactory)
    age_group = factory.SubFactory(AgeGroupFactory)
    demand_rate_set = factory.SubFactory(DemandRateSetFactory)
