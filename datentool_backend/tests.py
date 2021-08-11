from hypothesis.extra.django import TestCase, from_model
from hypothesis import given
from hypothesis.strategies import integers, lists, just
from .models import Years, Raster, RasterCell



class PopulationTestCase(TestCase):

    @given(from_model(Years, year=integers(min_value=2000, max_value=2100)))
    def test_years(self, year):
        self.assertIsInstance(year, Years)
        self.assertIsNotNone(year.pk)
        self.assertGreaterEqual(year.year, 2000)
        self.assertLessEqual(year.year, 2100)

    @given(from_model(Raster, year=from_model(Years)))
    def test_raster(self, raster):
        self.assertIsInstance(raster, Raster)
        self.assertIsNotNone(raster.pk)

    def generate_with_cells(raster):
        return lists(from_model(RasterCell, raster=just(raster)),
                     min_size=2,
                     max_size=8).map(lambda _: raster)

    @given(
        from_model(Raster, year=from_model(Years)).
        flatmap(generate_with_cells)
    )
    def test_raster_cells(self, raster):
        self.assertIsInstance(raster, Raster)
        self.assertIsNotNone(raster.pk)
        self.assertLessEqual(raster.rastercell_set.count(), 8)
        cell = raster.rastercell_set.first()
        self.assertLessEqual(len(cell.cellcode), 12)
