import numpy as np
from django.contrib.gis.geos import Point, Polygon
from faker import Faker
import factory
from factory.django import DjangoModelFactory
from .models import (Year, Raster, PopulationRaster,
                     RasterCell, RasterCellPopulation,
                     Gender, AgeGroup,
                     DisaggPopRaster, RasterCellPopulationAgeGender,
                     Prognosis, PrognosisEntry,
                     Population, PopulationEntry,
                     PopStatistic, PopStatEntry,
                     )
from ..area.factories import AreaFactory, AreaLevelFactory

faker = Faker('de-DE')

class YearFactory(DjangoModelFactory):
    class Meta:
        model = Year

    year = faker.unique.year()


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
    poly_wgs = poly.transform(4326, clone=True)
    return poly_wgs


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
        django_get_or_create = ('raster', )

    raster = factory.SubFactory(PopulationRasterFactory)
    cell = factory.SubFactory(RasterCellFactory)
    value = faker.pyfloat(max_value=100)


class GenderFactory(DjangoModelFactory):
    class Meta:
        model = Gender

    name = factory.Sequence(lambda n: faker.unique.word())


#class AgeClassificationFactory(DjangoModelFactory):
    #class Meta:
        #model = AgeClassification

    #name = faker.word()

    #@factory.post_generation
    #def agegroups(self, create, extracted, **kwargs):
        #if not create:
            ## Simple build, do nothing.
            #return

        #n_agegroups = faker.pyint(min_value=1, max_value=10)
        #limits = np.random.choice(np.arange(1, 128), (n_agegroups, ), False)
        #limits.sort()
        #start = 0
        #age_groups = []
        #for end in limits:
            #age_groups.append(
                #AgeGroup(classification=self, from_age=start, to_age=end - 1))
            #start = end
        #AgeGroup.objects.bulk_create(age_groups)


class AgeGroupFactory(DjangoModelFactory):
    class Meta:
        model = AgeGroup

    from_age = faker.pyint(max_value=127)
    to_age = faker.pyint(max_value=127)


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
    age = faker.pyint(max_value=127)
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
    age = faker.pyint(max_value=127)
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
    age = faker.pyint(max_value=127)
    immigration = faker.pyfloat(positive=True)
    emigration = faker.pyfloat(positive=True)
    births = faker.pyfloat(positive=True)
    deaths = faker.pyfloat(positive=True)
