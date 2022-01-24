from factory.django import DjangoModelFactory
from django.contrib.gis.geos import Point

from datentool_backend.utils.geometry_fields import get_point_from_latlon

from .models import (Scenario,
                     Place,
                     Capacity,
                     FieldTypes,
                     FieldType,
                     FClass,
                     PlaceField,
                     )

from datentool_backend.user.factories import (PlanningProcessFactory,
                                              InfrastructureFactory,
                                              ServiceFactory,
                                              )
from datentool_backend.population.factories import PrognosisFactory

import factory
from faker import Faker
faker = Faker('de-DE')


class ScenarioFactory(DjangoModelFactory):
    class Meta:
        model = Scenario

    name = faker.word()
    planning_process = factory.SubFactory(PlanningProcessFactory)
    prognosis = factory.SubFactory(PrognosisFactory)


class PlaceFactory(DjangoModelFactory):
    """location of an infrastructure"""
    class Meta:
        model = Place

    name = faker.unique.word()
    infrastructure = factory.SubFactory(InfrastructureFactory)
    geom = get_point_from_latlon(faker.latlng(), 3857)
    attributes = faker.json(num_rows=3, indent=True)


class CapacityFactory(DjangoModelFactory):
    """Capacity of an infrastructure for a service"""
    class Meta:
        model=Capacity

    place = factory.SubFactory(PlaceFactory)
    service = factory.SubFactory(ServiceFactory)
    capacity = faker.pyfloat(positive=True)
    from_year = 0


class FieldTypeFactory(DjangoModelFactory):
    """a generic field type"""
    class Meta:
        model = FieldType

    field_type = faker.random_element(FieldTypes)
    name = faker.word()


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
    sensitive = faker.pybool()
