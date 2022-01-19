from faker import Faker
import factory
from factory.django import DjangoModelFactory
from .models import (Mode, ModeVariant, Router, Stop,
                     MatrixCellPlace, MatrixCellStop, MatrixPlaceStop,
                     MatrixStopStop, Indicator, IndicatorTypes, CutOffTime)
from datentool_backend.infrastructure.models import (Infrastructure)
from ..population.factories import RasterCellFactory
from ..infrastructure.factories import (ServiceFactory, PlaceFactory,
                                        InfrastructureFactory)


faker = Faker('de-DE')


class ModeFactory(DjangoModelFactory):
    class Meta:
        model = Mode

    name = factory.Sequence(lambda n: faker.unique.name())


class ModeVariantFactory(DjangoModelFactory):
    class Meta:
        model = ModeVariant

    mode = factory.SubFactory(ModeFactory)
    name = factory.LazyAttribute(lambda o: f'{o.mode.name}_Variant')
    meta = faker.json(num_rows=3, indent=True)
    is_default = faker.pybool()


class StopFactory(DjangoModelFactory):
    class Meta:
        model = Stop

    mode = factory.SubFactory(ModeFactory)
    name = faker.word()


# class MatrixCellPlaceFactory(DjangoModelFactory):
    # class Meta:
        #model = MatrixCellPlace
        #django_get_or_create = ('cell', 'place', 'variant')

    #cell = factory.SubFactory(RasterCellFactory)
    #place = factory.SubFactory(PlaceFactory)
    #variant = factory.SubFactory(ModeVariantFactory)
    #minutes = faker.pyfloat(positive=True, max_value=100)


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


class CutOffTimeFactory(DjangoModelFactory):
    class Meta:
        model = CutOffTime
    mode_variant = factory.SubFactory(ModeVariantFactory)
    infrastructure = factory.SubFactory(InfrastructureFactory)
    minutes = faker.pyfloat()


#class MatrixCellStopFactory(DjangoModelFactory):
    #class Meta:
        #model = MatrixCellStop
    #cell = factory.SubFactory(RasterCellFactory)
    #stop = factory.SubFactory(StopFactory)
    #variant = factory.SubFactory(ModeVariantFactory)
    #minutes = faker.pyfloat(positive=True)



