from typing import List

import pandas as pd

import mapbox_vector_tile
from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from ..factories import IndicatorFactory

from ..compute import (ComputePopulationAreaIndicator,
                      )

from .setup_testdata import CreateInfrastructureTestdataMixin
from datentool_backend.population.models import Population, DisaggPopRaster, PopulationEntry


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

        # disaggregate the population
        response = self.get('populations-disaggregate', pk=population.pk)
        self.assertTrue(response.data.get('valid'))
        # do again to check updates
        response = self.get('populations-disaggregate', pk=population.pk)
        self.assertTrue(response.data.get('valid'))

        # get disaggregated population
        response = self.get_check_200(url = 'disaggpoprasters-detail',
                                      pk=population.raster.pk)
        df = pd.DataFrame.from_records(response.data['rastercellpopulationagegender_set'])

        # compare to population entry
        popentries = PopulationEntry.objects.filter(population=population)
        df_popentries = pd.DataFrame.from_records(
            popentries.values('area', 'gender', 'age_group', 'value'))

        # check by gender
        expected = df_popentries[['gender', 'value']].groupby('gender').sum()
        actual = df[['gender', 'value']].groupby('gender').sum()
        pd.testing.assert_frame_equal(actual, expected)

        # check by age_group
        expected = df_popentries[['age_group', 'value']].groupby('age_group').sum()
        actual = df[['age_group', 'value']].groupby('age_group').sum()
        pd.testing.assert_frame_equal(actual, expected)

        # check by cell
        actual = df[['cell', 'value']].groupby('cell').sum()




    def test_persons_in_area(self):
        """Test the number of persons by area and year"""
