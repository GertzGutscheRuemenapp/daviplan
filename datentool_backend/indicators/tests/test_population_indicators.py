from typing import List

import mapbox_vector_tile
from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from ..factories import IndicatorFactory

from ..compute import (ComputePopulationAreaIndicator,
                      )

from .setup_testdata import CreateInfrastructureTestdataMixin
from datentool_backend.population.models import Population, DisaggPopRaster


class TestAreaIndicatorAPI(CreateInfrastructureTestdataMixin,
                           LoginTestCase,
                           APITestCase):
    """Test to get an area indicator"""
    url_key = "areaindicators"

    @property
    def query_params(self):
        return {'indicator': self.indicator.pk,
                'area_level': self.area1.area_level.pk, }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.indicator = IndicatorFactory(
            indicator_type__classname=ComputePopulationAreaIndicator.__name__)

        cls.create_areas()
        cls.create_years_gender_agegroups()
        cls.create_raster_population()
        cls.create_population()
        cls.create_scenario()

    def test_disaggregate_population(self):
        """Test if the population is correctly Disaggregated to RasterCells"""
        population: Population = self.population
        self.get('populations-disaggregate', pk=population.pk)

        response = self.get(url_name = 'disaggpoprasters-detail',
                            pk=population.raster.pk)


    def test_persons_in_area(self):
        """Test the number of persons by area and year"""
