import pandas as pd

from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from ..factories import IndicatorFactory

from ..compute import (ComputePopulationAreaIndicator,
                      )

from .setup_testdata import CreateInfrastructureTestdataMixin
from datentool_backend.demand.models import AgeGroup, Gender
from datentool_backend.area.models import Area
from datentool_backend.population.models import (Population,
                                                 RasterCellPopulation,
                                                 PopulationEntry)


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

    def test_area_without_rasterpopulation(self):
        """
        Test what happens, if there is population in an area,
        but no rastercells with values to distribute
        """
        #delete the existing cellcodes in area3
        cellcodes_area3 = [f'100mN{n:05}E{e:05}'
                           for n, e in
                           [(30226, 42482), (30227, 42483)]]
        rcp = RasterCellPopulation.objects.filter(cell__cellcode__in=cellcodes_area3)
        rcp.delete()

        #add a population entries in area3
        area3 = Area.objects.get(attributes__gen='area3')
        age_group = AgeGroup.objects.first()
        gender = Gender.objects.first()
        PopulationEntry.objects.create(population=self.population,
                                       area=area3,
                                       age_group=age_group,
                                       gender=gender,
                                       value=444)
        gender = Gender.objects.last()
        PopulationEntry.objects.create(population=self.population,
                                       area=area3,
                                       age_group=age_group,
                                       gender=gender,
                                       value=555)

        # Disaggregate the population
        response = self.get('populations-disaggregate', pk=self.population.pk)
        self.assertTrue(response.data.get('valid'))
        # there should be a message about the not distributed inhabitants
        self.assertIn('999.0 Inhabitants not located to rastercells', response.data.get('message'))
        self.assertIn('area3', response.data.get('message'))

        # get disaggregated population
        response = self.get_check_200(url='disaggpoprasters-detail',
                                      pk=self.population.raster.pk)
        df = pd.DataFrame.from_records(response.data['rastercellpopulationagegender_set'])

        # compare to population entry
        popentries = PopulationEntry.objects.filter(population=self.population)
        df_popentries = pd.DataFrame.from_records(
            popentries.values('area', 'gender', 'age_group', 'value'))

        # check results by gender, ignore population in area3
        expected = df_popentries.loc[df_popentries.area != area3.id]\
            [['gender', 'value']]\
            .groupby('gender')\
            .sum()
        actual = df[['gender', 'value']].groupby('gender').sum()
        pd.testing.assert_frame_equal(actual, expected)

        # Delete area2+3 with its population
        area_2_and_3 = Area.objects.filter(attributes__gen__in=['area2', 'area3'])
        area_2_and_3.delete()

        # Disaggregate the population
        response = self.get('populations-disaggregate', pk=self.population.pk)
        self.assertTrue(response.data.get('valid'))

        # get disaggregated population
        response = self.get_check_200(url = 'disaggpoprasters-detail',
                                      pk=self.population.raster.pk)
        df = pd.DataFrame.from_records(response.data['rastercellpopulationagegender_set'])

        # compare to population entry
        popentries = PopulationEntry.objects.filter(population=self.population)
        df_popentries = pd.DataFrame.from_records(
            popentries.values('area', 'gender', 'age_group', 'value'))

        # check by gender
        expected = df_popentries[['gender', 'value']].groupby('gender').sum()
        actual = df[['gender', 'value']].groupby('gender').sum()
        pd.testing.assert_frame_equal(actual, expected)

