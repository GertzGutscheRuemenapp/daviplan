from faker import Factory
from faker.generator import Generator
import factory
from factory.django import DjangoModelFactory
from .models import (Infrastructure, Quota, Service)
from ..user.factories import ProfileFactory
from ..area.factories import InternalWFSLayerFactory, MapSymbolsFactory

faker: Generator = Factory.create()


class InfrastructureFactory(DjangoModelFactory):
    class Meta:
        model = Infrastructure
    name = faker.word()
    description = faker.sentence()
    #editable_by = models.ManyToManyField(
        #Profile, related_name='infrastructure_editable_by')
    #accessible_by = models.ManyToManyField(
        #Profile, related_name='infrastructure_accessible_by')
    # sensitive_data
    layer = factory.SubFactory(InternalWFSLayerFactory)
    symbol = factory.SubFactory(MapSymbolsFactory)


class QuotaFactory(DjangoModelFactory):
    class Meta:
        model = Quota
    quota_type = faker.word()


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = Service
    name = faker.word()
    description = faker.sentence()
    infrastructure = factory.SubFactory(InfrastructureFactory)
    #editable_by
    capacity_singular_unit = faker.word()
    capacity_plural_unit = faker.word()
    has_capacity = True
    demand_singular_unit = faker.word()
    demand_plural_unit = faker.word()
    quota = factory.SubFactory(QuotaFactory)
