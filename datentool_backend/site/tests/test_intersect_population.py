from test_plus import APITestCase
from django.contrib.gis.geos import MultiPolygon
from django.db.models import Sum

from datentool_backend.api_test import (LoginTestCase
                                        )
from datentool_backend.population.models import (RasterCell, RasterCellPopulation)
from datentool_backend.population.factories import (PopulationRaster,
                                                    RasterFactory,
                                                    YearFactory)

from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin

class TestIntersectZensus(CreateTestdataMixin,
                          LoginTestCase,
                          APITestCase):
    """test the intersection with Zensus Data"""
    url_key = "fixedindicators"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()
        cls.projectsettings = cls.create_project_settings()
        year = YearFactory(year=2011)
        raster = RasterFactory(name='LAEA-Raster')
        cls.popraster100 = PopulationRaster.objects.create(
            raster=raster,
            name='Zensus 2011 100m',
            filename='Zensus2011Einwohner100_LAEA3035.tif',
            default=True)
        raster4326 = RasterFactory(name='laea4326')
        cls.popraster500 = PopulationRaster.objects.create(
            raster=raster4326,
            name='Zensus 2011 500m',
            filename='Zensus2011Einwohner500.tif',
            default=False)

    def test_intersect_population(self):
        """test intersection with population"""
        response = self.post('populationrasters-intersect-census',
                             pk=self.popraster100.pk, extra={'format': 'json'})
        self.assert_http_202_accepted(response, response.data)

        expected_population = 37710
        expected_cells = 1113

        self.assertEqual(RasterCell.objects.filter(raster=self.popraster100.raster).count(),
                         expected_cells)
        self.assertEqual(RasterCellPopulation.objects\
            .filter(popraster=self.popraster100)\
            .count(),
            expected_cells)
        value_sum = RasterCellPopulation.objects\
            .filter(popraster=self.popraster100)\
            .aggregate(Sum('value'))
        self.assertAlmostEqual(value_sum['value__sum'], expected_population)

        response = self.post('populationrasters-intersect-census',
                             pk=self.popraster500.pk,
                             extra={'format': 'json'})
        self.assert_http_202_accepted(response, response.data)

        expected_population = 36141
        expected_cells = 111

        self.assertEqual(RasterCell.objects.filter(raster=self.popraster500.raster).count(),
                         expected_cells)
        self.assertEqual(RasterCellPopulation.objects\
            .filter(popraster=self.popraster500)\
            .count(),
            expected_cells)
        value_sum = RasterCellPopulation.objects\
            .filter(popraster=self.popraster500)\
            .aggregate(Sum('value'))
        self.assertAlmostEqual(value_sum['value__sum'], expected_population)
