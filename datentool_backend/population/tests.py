from hypothesis.extra.django import TestCase, from_model
from hypothesis import given
from hypothesis.strategies import integers, lists, just
from .models import (Years, Raster, RasterCell,
                     Gender, AgeClassification, AgeGroup,
                     DisaggPopRaster)


def year():
    return from_model(Years, year=integers(min_value=2000, max_value=2100))


def raster():
    return from_model(Raster, year=year())


def gender():
    return from_model(Gender)


def age_classification():
    return from_model(AgeClassification)


def disagg_pop_raster():
    return from_model(DisaggPopRaster, raster=raster())


class PopulationTestCase(TestCase):

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

    def generate_with_cells(raster):
        return lists(from_model(RasterCell, raster=just(raster)),
                     min_size=2,
                     max_size=8).map(lambda _: raster)

    @given(raster().flatmap(generate_with_cells) )
    def test_raster_cells(self, raster: Raster):
        self.assertIsInstance(raster, Raster)
        self.assertIsNotNone(raster.pk)
        self.assertLessEqual(raster.rastercell_set.count(), 8)
        cell = raster.rastercell_set.first()
        self.assertLessEqual(len(cell.cellcode), 12)

    @given(from_model(AgeGroup, classification=age_classification()))
    def test_age_group(self, age_group: AgeGroup):
        self.assertIsInstance(age_group, AgeGroup)
        self.assertIsInstance(age_group.classification, AgeClassification)
        self.assertGreaterEqual(age_group.from_age, 0)
        self.assertGreaterEqual(age_group.to_age, 0)
        self.assertLessEqual(age_group.from_age, 127)
        self.assertLessEqual(age_group.to_age, 127)

    @given(lists(gender()))
    def test_genders(self, genders):
        for gender in genders:
            self.assertIsInstance(gender, Gender)

    #@given(disagg_pop_raster())
    #def test_disagg_pop_raster(self,
                               #disagg_pop_raster: DisaggPopRaster,
                               ##genders,
                               #):
        #self.assertIsInstance(disagg_pop_raster, DisaggPopRaster)
        #self.assertIsInstance(disagg_pop_raster.raster, Raster)
        ##disagg_pop_raster.genders.add(genders)
        ##self.assertIsInstance(disagg_pop_raster.genders, Gender)
