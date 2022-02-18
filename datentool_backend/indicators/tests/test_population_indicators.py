import pandas as pd

from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase

from datentool_backend.area.factories import AreaLevelFactory

from ..compute import (ComputePopulationAreaIndicator,
                       ComputePopulationDetailAreaIndicator,
                       )

from .setup_testdata import CreateInfrastructureTestdataMixin
from datentool_backend.demand.models import AgeGroup, Gender
from datentool_backend.area.models import Area, AreaAttribute
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
        cls.profile.can_edit_basedata = True
        cls.profile.save()

        cls.create_areas()
        cls.create_years_gender_agegroups()
        cls.create_raster_population()
        cls.create_population()
        cls.create_scenario()

    def test_intersect_areas_and_disaggregate(self):
        """Test intersect areas and disaggregate population"""
        population: Population = self.population

        area_level3 = AreaLevelFactory()
        # disaggregate the population, but no areas in arealevel
        response = self.get('populations-intersectareaswithcells',
                            pk=population.pk,
                            data={'area_level': area_level3.pk,
                                  'drop_constraints': False, })
        self.assert_http_202_accepted(response)
        self.assertEqual(response.data.get('message'), 'No areas available')

        # disaggregate the population and use precalculated rastercells
        response = self.get('populations-intersectareaswithcells',
                            pk=population.pk,
                            data={'drop_constraints': False,})
        self.assert_http_202_accepted(response)
        print(response.data.get('message'))

        # disaggregate the population and use precalculated rastercells
        response = self.get('populations-disaggregate', pk=population.pk,
                            data={'use_intersected_data': True,
                                  'drop_constraints': False, })
        self.assert_http_202_accepted(response)
        print(response.data.get('message'))

        unknown_population = max(Population.objects.all().values_list('id', flat=True)) + 1
        response = self.get('populations-intersectareaswithcells',
                            pk=unknown_population,
                            data={'drop_constraints': False,})
        self.assert_http_406_not_acceptable(response)

    def test_disaggregate_population(self):
        """Test if the population is correctly Disaggregated to RasterCells"""
        population: Population = self.population

        # disaggregate the population
        response = self.get('populations-disaggregate', pk=population.pk,
                            data={'drop_constraints': False, })
        self.assert_http_202_accepted(response)
        print(response.data.get('message'))
        # do again to check updates
        response = self.get('populations-disaggregate', pk=population.pk,
                            data={'drop_constraints': False, })
        self.assert_http_202_accepted(response)

        # get disaggregated population
        response = self.get_check_200(url='populations-get-details',
                                      pk=population.pk)
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

        # disaggregate the population
        response = self.get('populations-disaggregateall',
                            data={'drop_constraints': False, })
        self.assert_http_202_accepted(response)
        print(response.data.get('message'))

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
        area3 = AreaAttribute.objects.get(field__name='gen', str_value='area3').area
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
        response = self.get('populations-disaggregate', pk=self.population.pk,
                            data={'drop_constraints': False,})
        self.assert_http_202_accepted(response)
        # there should be a message about the not distributed inhabitants
        self.assertIn('999.0 Inhabitants not located to rastercells',
                      response.data.get('message'))
        self.assertIn('area3', response.data.get('message'))

        # get disaggregated population
        response = self.get_check_200(url='populations-get-details',
                                      pk=self.population.pk)
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
        aa2_and_3 = AreaAttribute.objects.filter(field__name='gen',
                                                 str_value__in=['area2', 'area3'])
        area_2_and_3 = Area.objects.filter(id__in=aa2_and_3.values('area'))
        area_2_and_3.delete()

        # Disaggregate the population
        response = self.get('populations-disaggregate', pk=self.population.pk,
                            data={'drop_constraints': False,})
        self.assert_http_202_accepted(response)

        # get disaggregated population
        response = self.get_check_200(url = 'populations-get-details',
                                      pk=self.population.pk)
        df = pd.DataFrame.from_records(response.data['rastercellpopulationagegender_set'])

        # compare to population entry
        popentries = PopulationEntry.objects.filter(population=self.population)
        df_popentries = pd.DataFrame.from_records(
            popentries.values('area', 'gender', 'age_group', 'value'))

        # check by gender
        expected = df_popentries[['gender', 'value']].groupby('gender').sum()
        actual = df[['gender', 'value']].groupby('gender').sum()
        pd.testing.assert_frame_equal(actual, expected)

    def test_aggregate_population_to_area(self):
        """Test the aggregation of population to areas of an area level"""
        populations = Population.objects.all()
        for population in populations:
            self.get('populations-disaggregate', pk=population.pk,
                            data={'drop_constraints': False,})
            self.get('populations-intersectareaswithcells', pk=population.pk,
                     data={'area_level': self.area_level2.pk,
                           'drop_constraints': False,})

        # create a compute indicator, if not yet exists

        response = self.get('indicators-list', data={
            'indicatortype_classname': ComputePopulationAreaIndicator.__name__})

        if not response.data:
            response = self.get('indicatortypes-list', data={
                'classname': ComputePopulationAreaIndicator.__name__})
            indicatortype_id = response.data[0]['id']

            response = self.post('indicators-list', data={
                'indicator_type': indicatortype_id,
                'name': 'MyComputePopAreaIndicator',
            })
            indicator_id = response.data['id']

        query_params = {'indicator': indicator_id,
                        'area_level': self.area_level2.pk, }

        response = self.get_check_200(self.url_key + '-aggregate-population', data=query_params)
        print(response.data)
        # Test if sum of large area equals all input areas

        # area_level1
        query_params = {'indicator': indicator_id,
                        'area_level': self.obj.pk, }

        response = self.get_check_200(self.url_key+'-aggregate-population', data=query_params)
        # Test if input data matches
        print(response.data)

        query_params = {'indicator': indicator_id,
                        'area_level': self.obj.pk,
                        'gender': self.genders[0].pk,
                        }

        response = self.get_check_200(self.url_key + '-aggregate-population', data=query_params)
        print(response.data)


        query_params = {'indicator': indicator_id,
                        'area_level': self.obj.pk,
                        'age_group': self.age_groups.values_list('id', flat=True)[:2],
                        }

        response = self.get_check_200(self.url_key + '-aggregate-population', data=query_params)
        print(response.data)

        query_params = {'indicator': indicator_id,
                        'area_level': self.obj.pk,
                        'area': [self.area1.pk, self.area3.pk],
                        }

        response = self.get_check_200(self.url_key + '-aggregate-population', data=query_params)
        print(response.data)


    def test_get_population_by_year_agegroup_gender(self):
        """Test to get the population by year, agegroup, and gender"""
        populations = Population.objects.all()
        for population in populations:
            self.get('populations-disaggregate', pk=population.pk,
                     data={'use_intersected_data': True,
                           'drop_constraints': False, })
            self.get('populations-intersectareaswithcells', pk=population.pk,
                     data={'area_level': self.area_level2.pk,
                     'use_intersected_data': True,
                     'drop_constraints': False, })

        # create a compute indicator, if not yet exists

        response = self.get('indicators-list', data={
            'indicatortype_classname':
            ComputePopulationDetailAreaIndicator.__name__})

        if not response.data:
            response = self.get('indicatortypes-list', data={
                'classname': ComputePopulationDetailAreaIndicator.__name__})
            indicatortype_id = response.data[0]['id']

            response = self.post('indicators-list', data={
                'indicator_type': indicatortype_id,
                'name': 'MyComputePopAreaIndicator',
            })
            indicator_id = response.data['id']

        query_params = {'indicator': indicator_id,
                        'area': self.area1.pk, }

        response = self.get_check_200('populationindicators-population-details', data=query_params)
        print(response.data)
        # Test if sum of large area equals all input areas

        # area_level2
        query_params = {'indicator': indicator_id,
                        'area': self.district1.pk, }

        response = self.get_check_200('populationindicators-population-details', data=query_params)
        # Test if input data matches
        print(response.data)

        # area_level2 and prognosis
        query_params = {'indicator': indicator_id,
                        'area': self.district1.pk,
                        'prognosis': self.prognosis.pk,}

        response = self.get_check_200('populationindicators-population-details', data=query_params)
        # Test if input data matches
        print(response.data)
