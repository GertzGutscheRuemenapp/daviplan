from faker import Faker
import factory
from factory.django import DjangoModelFactory
from .models import AgeGroup, Gender, DemandRateSet, DemandRate
from datentool_backend.infrastructure.factories import ServiceFactory
from datentool_backend.site.factories import YearFactory

faker = Faker('de-DE')


class GenderFactory(DjangoModelFactory):
    class Meta:
        model = Gender

    name = factory.Sequence(lambda n: faker.unique.word())


class AgeGroupFactory(DjangoModelFactory):
    class Meta:
        model = AgeGroup

    from_age = faker.pyint(max_value=127)
    to_age = faker.pyint(max_value=127)


class DemandRateSetFactory(DjangoModelFactory):
    class Meta:
        model = DemandRateSet
    name = faker.word()
    is_default = faker.pybool()
    service = factory.SubFactory(ServiceFactory)


class DemandRateFactory(DjangoModelFactory):
    class Meta:
        model = DemandRate
    year = factory.SubFactory(YearFactory)
    age_group = factory.SubFactory(AgeGroupFactory)
    gender = factory.SubFactory(GenderFactory)
    demand_rate_set = factory.SubFactory(DemandRateSetFactory)
    value = faker.pyfloat()
