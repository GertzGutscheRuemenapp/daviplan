import factory
from factory.django import DjangoModelFactory

from datentool_backend.utils.geometry_fields import get_point_from_latlon

from .models import (Router, Stop, MatrixCellPlace, MatrixCellStop,
                    MatrixPlaceStop, MatrixStopStop)

from datentool_backend.modes.factories import ModeVariantFactory
from datentool_backend.infrastructure.factories import PlaceFactory
from datentool_backend.population.factories import RasterCellFactory

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


class MatrixCellPlaceFactory(DjangoModelFactory):
    class Meta:
        model = MatrixCellPlace
    cell = factory.SubFactory(RasterCellFactory)
    place = factory.SubFactory(PlaceFactory)
    variant = factory.SubFactory(ModeVariantFactory)
    minutes = faker.pyfloat()


class MatrixCellStopFactory(DjangoModelFactory):
    class Meta:
        model = MatrixCellStop
    cell = factory.SubFactory(RasterCellFactory)
    stop = factory.SubFactory(StopFactory)
    variant = factory.SubFactory(ModeVariantFactory)
    minutes = faker.pyfloat()


class MatrixPlaceStopFactory(DjangoModelFactory):
    class Meta:
        model = MatrixPlaceStop
    place = factory.SubFactory(PlaceFactory)
    stop = factory.SubFactory(StopFactory)
    variant = factory.SubFactory(ModeVariantFactory)
    minutes = faker.pyfloat()


class MatrixStopStopFactory(DjangoModelFactory):
    class Meta:
        model = MatrixStopStop
    from_stop = factory.SubFactory(StopFactory)
    to_stop = factory.SubFactory(StopFactory)
    variant = factory.SubFactory(ModeVariantFactory)
    minutes = faker.pyfloat()
