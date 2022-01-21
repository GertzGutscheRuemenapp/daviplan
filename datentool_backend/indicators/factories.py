import factory
from factory.django import DjangoModelFactory

from datentool_backend.utils.geometry_fields import get_point_from_latlon

from .models import (ModeVariant, Router, Stop,
                    Indicator, IndicatorTypes)

from datentool_backend.modes.factories import ModeFactory
from datentool_backend.user.factories import (InfrastructureFactory,
                                              ServiceFactory,
                                              )

from faker import Faker
faker = Faker('de-DE')


class StopFactory(DjangoModelFactory):
    class Meta:
        model = Stop

    geom = get_point_from_latlon(faker.latlng(), 3857)
    name = faker.word()


class RouterFactory(DjangoModelFactory):
    class Meta:
        model = Router
    name = faker.word()
    osm_file = faker.file_path()
    tiff_file = faker.file_path()
    gtfs_file = faker.file_path()
    build_date = faker.date()
    buffer = faker.random_number(digits=2)


class IndicatorFactory(DjangoModelFactory):
    class Meta:
        model = Indicator
    indicator_type = faker.random_element(IndicatorTypes)
    name = faker.word()
    parameters = faker.json(num_rows=3, indent=True)
    service = factory.SubFactory(ServiceFactory)
