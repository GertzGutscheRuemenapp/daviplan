from faker import Faker
import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import Point
from .models import (Infrastructure, Service, Place,
                     Capacity, FieldTypes, FieldType, FClass, PlaceField,
                     Profile, ScenarioPlace, ScenarioCapacity)
from ..area.factories import InternalWFSLayerFactory, MapSymbolsFactory

faker = Faker('de-DE')


class InfrastructureFactory(DjangoModelFactory):
    class Meta:
        model = Infrastructure
    name = faker.word()
    description = faker.sentence()
    # sensitive_data
    layer = factory.SubFactory(InternalWFSLayerFactory)
    symbol = factory.SubFactory(MapSymbolsFactory)

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


class PlaceFactory(DjangoModelFactory):
    """location of an infrastructure"""
    class Meta:
        model = Place

    name = faker.unique.word()
    infrastructure = factory.SubFactory(InfrastructureFactory)
    geom = Point((faker.latlng()[1], faker.latlng()[0]))
    attributes = faker.json(num_rows=3, indent=True)


class ScenarioPlaceFactory(DjangoModelFactory):
    """location of an infrastructure in a scenario"""
    class Meta:
        model = ScenarioPlace

    scenario = faker.word()
    status_quo = faker.word()


class CapacityFactory(DjangoModelFactory):
    """Capacity of an infrastructure for a service"""
    class Meta:
        model = Capacity

    place = factory.SubFactory(PlaceFactory)
    service = factory.SubFactory(ServiceFactory)
    capacity = faker.pyfloat(positive=True)
    from_year = faker.year()


class ScenarioCapacityFactory(DjangoModelFactory):
    """capacity of an infrastructure for a service"""
    class Meta:
        model = ScenarioCapacity

    scenario = faker.word()
    status_quo = faker.pyint()


class FieldTypeFactory(DjangoModelFactory):
    """a generic field type"""
    class Meta:
        model = FieldType

    field_type = faker.random_element(FieldTypes)
    name = faker.word()

    #@factory.post_generation
    #def fclass_set(self, create, extracted, **kwargs):
        #if not create or self.field_type != FieldTypes.CLASSIFICATION:
            ## Simple build, do nothing.
            #return

        #if extracted:
            ## A list of fclasses were passed in, use them
            #for fclass in extracted:
                #self.fclass_set.add(fclass)
        #else:
            #fclass = FClass.objects.first()
            #if fclass is not None:
                #self.fclass_set.add(fclass)


class FClassFactory(DjangoModelFactory):
    """a class in a classification"""
    class Meta:
        model = FClass

    classification = factory.SubFactory(FieldTypeFactory)
    order = factory.Sequence(lambda n: faker.unique.pyint(max_value=100))
    value = faker.unique.word()


class PlaceFieldFactory(DjangoModelFactory):
    """a field of a place"""
    class Meta:
        model = PlaceField

    attribute = faker.unique.word()
    unit = faker.word()
    infrastructure = factory.SubFactory(InfrastructureFactory)
    field_type = factory.SubFactory(FieldTypeFactory)
