from factory.django import DjangoModelFactory

from datentool_backend.utils.geometry_fields import get_point_from_latlon
from datentool_backend.area.factories import FieldTypeFactory

from .models import (Scenario,
                     Place,
                     Capacity,
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
    attributes = {'firstname': faker.name(), 'employees': faker.pyint(),}


class CapacityFactory(DjangoModelFactory):
    """Capacity of an infrastructure for a service"""
    class Meta:
        model=Capacity

    place = factory.SubFactory(PlaceFactory)
    service = factory.SubFactory(ServiceFactory)
    capacity = faker.pyfloat(positive=True)
    from_year = 0


class PlaceFieldFactory(DjangoModelFactory):
    """a field of a place"""
    class Meta:
        model = PlaceField

    name = faker.unique.word()
    unit = faker.word()
    infrastructure = factory.SubFactory(InfrastructureFactory)
    field_type = factory.SubFactory(FieldTypeFactory)
    sensitive = faker.pybool()
