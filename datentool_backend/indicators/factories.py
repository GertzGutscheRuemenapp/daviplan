from faker import Faker
import factory
from factory.django import DjangoModelFactory
from .models import (Modes, ModeVariant, Router,
                     ReachabilityMatrix, Indicator, IndicatorTypes)

from ..population.factories import RasterCellFactory
from ..infrastructure.factories import ServiceFactory


faker = Faker('de-DE')


class ModeFactory(DjangoModelFactory):
    class Meta:
        model = Modes

    name = factory.Sequence(lambda n: faker.unique.name())


class ModeVariantFactory(DjangoModelFactory):
    class Meta:
        model = ModeVariant

    mode = factory.SubFactory(ModeFactory)
    name = factory.LazyAttribute(lambda o: f'{o.mode.name}_Variant')
    meta = faker.json(num_rows=3, indent=True)
    is_default = faker.pybool()


class ReachabilityMatrixFactory(DjangoModelFactory):
    class Meta:
        model = ReachabilityMatrix
        django_get_or_create = ('from_cell', 'to_cell', 'variant')

    from_cell = factory.SubFactory(RasterCellFactory)
    to_cell = factory.SubFactory(RasterCellFactory)
    variant = factory.SubFactory(ModeVariantFactory)
    minutes = faker.pyfloat(positive=True, max_value=100)


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