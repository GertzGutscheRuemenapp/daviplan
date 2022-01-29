import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import Point, Polygon

from .models import (Raster, PopulationRaster,
                     RasterCell, RasterCellPopulation,
                     DisaggPopRaster, RasterCellPopulationAgeGender,
                     Prognosis, PrognosisEntry,
                     Population, PopulationEntry,
                     PopStatistic, PopStatEntry,
                     )
from datentool_backend.area.factories import AreaFactory, AreaLevelFactory
from datentool_backend.user.factories import YearFactory
from datentool_backend.demand.factories import AgeGroupFactory, GenderFactory

from faker import Faker
faker = Faker('de-DE')

class RasterFactory(DjangoModelFactory):
    class Meta:
        model = Raster

    name = faker.word()


class PopulationRasterFactory(DjangoModelFactory):
    class Meta:
        model = PopulationRaster
        django_get_or_create = ('year', 'raster')

    name = faker.word()
    raster = factory.SubFactory(RasterFactory)
    year = factory.SubFactory(YearFactory)


def _get_poly_from_cellcode(rc: 'RasterCell') -> Polygon:
    """convert cellcode to polygon"""
    north = int(rc.cellcode[5:10])
    east = int(rc.cellcode[11:16])
    offsets = [(0, 0), (0, 100), (100, 100), (100, 0), (0, 0)]
    points = [Point(x=east * 100 + dx, y=north * 100 + dy, srid=3035)
              for dx, dy in offsets]
    poly = Polygon(points, srid=3035)
    poly_webmercator = poly.transform(3857, clone=True)
    return poly_webmercator


def _get_point_from_poly(rc: 'RasterCell') -> Point:
    """convert polygon to point"""
    pnt = rc.poly.centroid
    return pnt


class RasterCellFactory(DjangoModelFactory):
    class Meta:
        model = RasterCell
        django_get_or_create = ('raster', )

    raster = factory.SubFactory(RasterFactory)
    cellcode = faker.pystr_format(string_format=f'100mN#####E#####')
    poly = factory.LazyAttribute(_get_poly_from_cellcode)
    pnt = factory.LazyAttribute(_get_point_from_poly)


class RasterCellPopulationFactory(DjangoModelFactory):
    class Meta:
        model = RasterCellPopulation
        #django_get_or_create = ('popraster', )

    popraster = factory.SubFactory(PopulationRasterFactory)
    cell = factory.SubFactory(RasterCellFactory)
    value = faker.pyfloat(max_value=100)


class DisaggPopRasterFactory(DjangoModelFactory):
    class Meta:
        model = DisaggPopRaster

    popraster = factory.SubFactory(PopulationRasterFactory)

    @factory.post_generation
    def genders(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of genders were passed in, use them
            for gender in extracted:
                self.genders.add(gender)


class RasterCellPopulationAgeGenderFactory(DjangoModelFactory):
    class Meta:
        model = RasterCellPopulationAgeGender

    disaggraster = factory.SubFactory(DisaggPopRasterFactory)
    year = faker.year()
    cell = factory.LazyAttribute(lambda o:
        RasterCellFactory(raster=o.disaggraster.popraster.raster))
    age_group =  factory.SubFactory(AgeGroupFactory)
    gender = factory.SubFactory(GenderFactory)
    value = faker.pyfloat(positive=True)


class PrognosisFactory(DjangoModelFactory):
    class Meta:
        model = Prognosis

    name = faker.unique.word()
    raster = factory.SubFactory(DisaggPopRasterFactory)
    is_default = faker.pybool()

    @factory.post_generation
    def years(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of years were passed in, use them
            for year in extracted:
                self.years.add(year)


class PrognosisEntryFactory(DjangoModelFactory):
    class Meta:
        model = PrognosisEntry

    prognosis = factory.SubFactory(PrognosisFactory)
    year = factory.SubFactory(YearFactory)
    area = factory.SubFactory(AreaFactory)
    agegroup = factory.SubFactory(AgeGroupFactory)
    gender = factory.SubFactory(GenderFactory)
    value = factory.Sequence(lambda n: faker.pyfloat(positive=True))


class PopulationFactory(DjangoModelFactory):
    class Meta:
        model = Population

    area_level = factory.SubFactory(AreaLevelFactory)
    year = factory.SubFactory(YearFactory)
    raster = factory.SubFactory(DisaggPopRasterFactory)

    @factory.post_generation
    def genders(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of genders were passed in, use them
            for gender in extracted:
                self.genders.add(gender)


class PopulationEntryFactory(DjangoModelFactory):
    class Meta:
        model = PopulationEntry

    population = factory.SubFactory(PopulationFactory)
    area = factory.SubFactory(AreaFactory)
    gender = factory.SubFactory(GenderFactory)
    age_group = factory.SubFactory(AgeGroupFactory)
    value = faker.pyfloat(positive=True)


class PopStatisticFactory(DjangoModelFactory):
    class Meta:
        model = PopStatistic

    year = factory.SubFactory(YearFactory)


class PopStatEntryFactory(DjangoModelFactory):
    class Meta:
        model = PopStatEntry

    popstatistic = factory.SubFactory(PopStatisticFactory)
    area = factory.SubFactory(AreaFactory)
    immigration = faker.pyfloat(positive=True)
    emigration = faker.pyfloat(positive=True)
    births = faker.pyfloat(positive=True)
    deaths = faker.pyfloat(positive=True)
