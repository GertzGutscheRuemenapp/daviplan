from typing import List
from hypothesis.extra.django import TestCase, from_model
from hypothesis import given
from hypothesis.strategies import integers, lists, just
from .models import (Years, Raster, RasterCell,
                     Gender, AgeClassification, AgeGroup,
                     DisaggPopRaster, RasterPopulationCell,
                     Prognosis, PrognosisEntry,
                     Area,
                     )
from ..area.tests import area


def year():
    return from_model(Years, year=integers(min_value=2000, max_value=2100))


def raster():
    return from_model(Raster, year=year())


def generate_with_cells(raster):
    return lists(from_model(RasterCell, raster=just(raster)),
                 min_size=2,
                 max_size=8).map(lambda _: raster)

def gender():
    return from_model(Gender)


def age_classification():
    return from_model(AgeClassification)


def generate_with_agegroups(age_classification):
    return lists(from_model(AgeGroup, classification=just(age_classification)),
                 min_size=2,
                 max_size=5).map(lambda _: age_classification)


def age_group():
    return from_model(AgeGroup, classification=age_classification())


def disagg_pop_raster():
    return from_model(DisaggPopRaster, raster=raster())


def prognosis():
    return from_model(
        Prognosis,
        raster=disagg_pop_raster(),
        age_classification=age_classification().flatmap(generate_with_agegroups))


class PopulationTestCase(TestCase):
    fixtures = ["areas.json"]

    @given(year())
    def test_years(self, year: Years):
        self.assertIsInstance(year, Years)
        self.assertIsNotNone(year.pk)
        self.assertGreaterEqual(year.year, 2000)
        self.assertLessEqual(year.year, 2100)

    @given(raster())
    def test_raster(self, raster: Raster):
        self.assertIsInstance(raster, Raster)
        self.assertIsNotNone(raster.pk)

    @given(raster().flatmap(generate_with_cells))
    def test_raster_cells(self, raster: Raster):
        self.assertIsInstance(raster, Raster)
        self.assertIsNotNone(raster.pk)
        print(raster.rastercell_set.count())
        #self.assertLessEqual(raster.rastercell_set.count(), 8)
        cell = raster.rastercell_set.first()
        self.assertLessEqual(len(cell.cellcode), 12)

    @given(age_group())
    def test_age_group(self, age_group: AgeGroup):
        self.assertIsInstance(age_group, AgeGroup)
        self.assertIsInstance(age_group.classification, AgeClassification)
        self.assertGreaterEqual(age_group.from_age, 0)
        self.assertGreaterEqual(age_group.to_age, 0)
        self.assertLessEqual(age_group.from_age, 127)
        self.assertLessEqual(age_group.to_age, 127)

    @given(lists(gender(), min_size=1))
    def test_genders(self, genders):
        for gender in genders:
            self.assertIsInstance(gender, Gender)

    @given(disagg_pop_raster(), lists(gender(), unique=True, min_size=1))
    def test_disagg_pop_raster(self,
                               disagg_pop_raster: DisaggPopRaster,
                               genders,
                               ):
        self.assertIsInstance(disagg_pop_raster, DisaggPopRaster)
        self.assertIsInstance(disagg_pop_raster.raster, Raster)
        disagg_pop_raster.genders.add(*genders)
        self.assertQuerysetEqual(disagg_pop_raster.genders.all(),
                                 genders,
                                 ordered=False)


    @given(raster().flatmap(generate_with_cells), disagg_pop_raster(), gender())
    def test_raster_population_cells(self,
                                     raster: Raster,
                                     disagg_pop_raster: DisaggPopRaster,
                          gender: Gender):
        disagg_pop_raster.genders.add(gender)
        for year in range(2000, 2015, 5):
            for cell in raster.rastercell_set.all():
                for age in range(10):
                    RasterPopulationCell.objects.create(raster=disagg_pop_raster,
                                                        year=year,
                                                        cell=cell,
                                                        age=age,
                                                        gender=gender,
                                                        value=42.3)

    @given(prognosis(),
           lists(year(), unique=True, min_size=1, max_size=10),
           lists(gender(), unique=True, min_size=1, max_size=3))
    def test_prognosis(self,
                       prognosis: Prognosis,
                       years: List[Years],
                       genders:List[Gender],
                       ):
        prognosis.years.add(*years)
        prognosis.raster.genders.add(*genders)
        areas = Area.objects.all()
        value = 0.0
        import time
        t0 = time.time()
        for year in years:
            for gender in prognosis.raster.genders.all():
                for agegroup in prognosis.age_classification.agegroup_set.all():
                    for area in areas:
                        value += 1.1
                        PrognosisEntry.objects.create(
                            prognosis=prognosis,
                            year=year,
                            gender=gender,
                            agegroup=agegroup,
                            area=area,
                            value=value,
                        )
        duration = time.time() - t0
        print(len(years), prognosis.raster.genders.count(),
              prognosis.age_classification.agegroup_set.count(), len(areas), f'{duration:0.3f}')


