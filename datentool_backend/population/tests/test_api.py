import os
import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(name='test')
from unittest import skip
from unittest.mock import Mock, patch
from django.test import TestCase
from test_plus import APITestCase

from datentool_backend.utils.regionalstatistik import Regionalstatistik
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin,
                                        LoginTestCase
                                        )
from datentool_backend.site.factories import YearFactory
from datentool_backend.population.models import (Year,
                                                 PopulationRaster,
                                                 PopulationEntry,
                                                 PopStatistic,
                                                 PopStatEntry,
                                                 Prognosis,
                                                 Population)
from datentool_backend.population.factories import (
    RasterCellFactory,
    AgeGroupFactory,
    GenderFactory,
    PopulationFactory,
    RasterCellPopulationFactory,
    RasterCellPopulationAgeGenderFactory,
    AreaFactory,
    PrognosisFactory,
    PopStatEntryFactory,
    RasterFactory,
    PopulationRasterFactory,
    PopulationEntryFactory,
    PopStatisticFactory
)
from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.area.factories import (AreaLevelFactory,
                                              AreaFactory,
                                              AreaFieldFactory,
                                              FieldTypes,
                                              FieldTypeFactory
                                              )
from datentool_backend.demand.factories import AgeGroupFactory, GenderFactory
from datentool_backend.demand.constants import RegStatAgeGroups

from faker import Faker

faker = Faker('de-DE')


class TestRegionalstatistikAPI(LoginTestCase, APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.admin_access = True
        cls.profile.save()

        cls.years = [YearFactory(year=y) for y in range(2012, 2015)]

        area_level = AreaLevelFactory(is_statistic_level=True)

        field_type = FieldTypeFactory(ftype=FieldTypes.STRING)
        AreaFieldFactory(name='gen',
                         area_level=area_level,
                         field_type=field_type,
                         is_label=True)
        AreaFieldFactory(name='ags',
                         area_level=area_level,
                         field_type=field_type,
                         is_key=True)

        AreaFactory(
            area_level=area_level,
            attributes={'ags': '01003000', 'gen': 'Lübeck'},
        )
        AreaFactory(
            area_level=area_level,
            attributes={'ags': '01053038', 'gen': 'Grinau'},
        )
        AreaFactory(
            area_level=area_level,
            attributes={'ags': '01053099', 'gen': 'Poggensee'},
        )
        cls.ags = [a.attributes.get(field__name='ags').value
                   for a in Area.objects.all()]
        cls.age_groups = [AgeGroupFactory(id=i + 1,
                                          from_age=r.from_age,
                                          to_age=r.to_age)
                          for i, r in enumerate(RegStatAgeGroups.agegroups)]

        cls.api = Regionalstatistik(start_year=2012, end_year=2014)
        for y in range(2012, 2015):
            year = Year.objects.get(year=y)
            year.is_real = True
            year.save()
        GenderFactory(id=1, name='männlich')
        GenderFactory(id=2, name='weiblich')


    # leave this skipped, because test_rest does the calls anyway,
    # only here for debugging
    @skip
    def test_genesis_pop_request(self):
        df = self.api.query_population(ags=self.ags)
        self.assertAlmostEqual(list(df['AGS'].unique()), self.ags)
        self.assertAlmostEqual(list(df['year'].unique()),
                               list(range(2012, 2015)))

    # same as above
    @skip
    def test_genesis_stats_request(self):
        df = self.api.query_migration(ags=self.ags)
        df = self.api.query_births(ags=self.ags)
        df = self.api.query_deaths(ags=self.ags)

    @patch('datentool_backend.utils.regionalstatistik.requests.get')
    def test_rest(self, mock_get):

        class MyMock(Mock):
            _testdatadir = os.path.join(os.path.dirname(__file__), 'data')
            _fnames = {Regionalstatistik.POP_CODE: 'population.ffcsv',
                       Regionalstatistik.MIGRATION_CODE: 'migration.ffcsv',
                       Regionalstatistik.BIRTHS_CODE: 'births.ffcsv',
                       Regionalstatistik.DEATHS_CODE: 'deaths.ffcsv',
                       }
            @property
            def text(self) -> str:
                code = self._get.call_args[1]['params']['name']
                fn = self._fnames.get(code)
                fftxt = open(os.path.join(self._testdatadir, fn)).read()
                return fftxt

        mock_get.return_value = MyMock(ok=True, status_code=200, _get=mock_get)
        res = self.post('populations-pull-regionalstatistik',
                        data={'drop_constraints': False, },
                        extra={'format': 'json'})

        popentries = pd.DataFrame(PopulationEntry.objects.values())

        actual = popentries.groupby(['area_id', 'population_id']).sum()['value']
        target = [211713, 212958, 214420, 311, 305, 315, 349, 335, 354]
        self.assertListEqual(list(actual), target)

        res = self.post('popstatistics-pull-regionalstatistik',
                        data={'drop_constraints': False, },
                        extra={'format': 'json'})

        popstatentries = pd.DataFrame(PopStatEntry.objects.values())

        actual = popstatentries.groupby(['area_id']).mean()\
            [['immigration', 'emigration', 'births', 'deaths']]
        target = pd.DataFrame.from_dict(
            {'immigration': [12061, 32, 35],
             'emigration': [10012, 13, 26],
             'births': [1813, 0.3, 4],
             'deaths': [2678, 16, 9]}).set_index(actual.index)
        pd.testing.assert_frame_equal(actual, target, atol=0.5, check_dtype=False)

        url = 'arealevels-detail'
        area_level = AreaLevel.objects.get(is_statistic_level=True)

        res = self.get(url, pk=area_level.pk)
        self.assert_http_200_ok(res)

        # check the max_values of the popstatentries
        popstatentries['nature_diff'] = (popstatentries['births'] -
                                         popstatentries['deaths']).apply(np.abs)

        popstatentries['migration_diff'] = (popstatentries['immigration'] -
                                         popstatentries['emigration']).apply(np.abs)

        target = popstatentries.max()\
            [['immigration', 'emigration',
              'births', 'deaths',
              'nature_diff', 'migration_diff']]
        actual = pd.Series(res.data['max_values'])
        pd.testing.assert_series_equal(actual.loc[target.index], target)

        # ToDo: permission test
        # ToDo: test user and password


class TestPopulation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.years = [YearFactory() for y in range(5)]
        cls.cell = RasterCellFactory()
        cls.genders = [GenderFactory() for i in range(3)]
        cls.population = PopulationFactory(genders=cls.genders)

    def test_cell(self):
        self.assertQuerysetEqual(
            self.population.genders.all(), self.genders, ordered=False)
        rp = RasterCellPopulationAgeGenderFactory()
        self.assertEqual(rp.cell.raster, rp.population.popraster.raster)
        str(rp.cell)

    def test_prognosis(self):
        """Test the prognosis"""
        pe = list()
        area = AreaFactory()
        popraster = PopulationRasterFactory()
        prognosis = PrognosisFactory()
        age_groups = [AgeGroupFactory(), AgeGroupFactory(), AgeGroupFactory()]
        years = self.years
        genders = [GenderFactory(), GenderFactory()]
        for year in years:
            population = PopulationFactory(prognosis=prognosis,
                                           year=year,
                                           genders=genders,
                                           popraster=popraster)
            for age_group in age_groups:
                for gender in genders:
                    pe.append(PopulationEntryFactory.build(
                        population=population,
                        area=area,
                        age_group=age_group,
                        gender=gender))

        PopulationEntry.objects.bulk_create(pe)
        pop_set = prognosis.population_set.all()
        values = np.array(pop_set.values_list('populationentry__value', flat=True)).\
            reshape(len(age_groups), len(years), len(genders))

    def test_prognosis_unique_default(self):
        prog1 = PrognosisFactory()
        prog2 = PrognosisFactory()
        prog3 = PrognosisFactory()
        prog4 = PrognosisFactory()

        prog1.is_default = True
        prog1.save()
        self.assertEqual(Prognosis.objects.get(is_default=True), prog1)

        prog3.is_default = True
        prog3.save()
        self.assertEqual(Prognosis.objects.get(is_default=True), prog3)

        prog2.is_default = True
        prog2.save()
        prog3.is_default = True
        prog3.save()
        prog4.is_default = True
        prog4.save()
        prog1.is_default = False
        prog1.save()
        self.assertEqual(Prognosis.objects.get(is_default=True), prog4)

    def test_popstatistic(self):
        ps = PopStatEntryFactory()

    def test_population(self):
        pop = PopulationFactory(genders=self.genders)
        self.assertQuerysetEqual(
            pop.genders.all(), self.genders, ordered=False)

    def test_raster_population(self):
        rcp = RasterCellPopulationFactory()
        logger.debug(rcp)


class TestRasterAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "rasters"
    factory = RasterFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.post_data = dict(name=faker.word())
        cls.put_data = dict(name=faker.word())
        cls.patch_data = dict(name=faker.word())


class TestPopulationRasterAPI(WriteOnlyWithCanEditBaseDataTest,
                              TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "populationrasters"
    factory = PopulationRasterFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        populationraster: PopulationRaster = cls.obj
        str(cls.obj)
        raster = populationraster.raster.pk

        data = dict(name=faker.word(), raster=raster, default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPrognosisAPI(WriteOnlyWithCanEditBaseDataTest,
                       TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "prognoses"
    factory = PrognosisFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(name=faker.word(), is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPopulationAPI(WriteOnlyWithCanEditBaseDataTest,
                        TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "populations"
    factory = PopulationFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        population: Population = cls.obj
        prognosis: Prognosis = population.prognosis.pk
        year = population.year.pk
        genders = list(population.genders.all().values_list(flat=True))
        popraster = population.popraster.pk

        data = dict(year=year, genders=genders,
                    popraster=popraster, prognosis=prognosis)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_years_with_population(self):
        """Test the route of years with population and prognosis """
        Year.objects.all().delete()
        for y in range(1910, 1930):
            Year.objects.create(year=y, is_default=(y==2020))
        for y in range(1910, 1921):
            year = Year.objects.get(year=y)
            Population.objects.create(year=year, prognosis=None)

        prognosis1 = Prognosis.objects.create(name='P1', is_default=True)
        prognosis2 = Prognosis.objects.create(name='P2', is_default=False)
        for y in range(1919, 1923):
            year = Year.objects.get(year=y)
            Population.objects.create(year=year, prognosis=prognosis1)
        for y in range(1927, 1930):
            year = Year.objects.get(year=y)
            Population.objects.create(year=year, prognosis=prognosis2)

        response = self.get_check_200(url='years-list')
        self.assertSetEqual({d['year'] for d in response.data},
                            set(range(1910, 1930)))

        response = self.get_check_200(url='years-list',
                                      data={'has_real_data': 1},)
        self.assertSetEqual({d['year'] for d in response.data},
                            set(range(1910, 1921)))

        response = self.get_check_200(url='years-list',
                                      data={'prognosis': prognosis1.pk},)
        self.assertSetEqual({d['year'] for d in response.data},
                            set(range(1919, 1923)))

        response = self.get_check_200(url='years-list',
                                      data={'prognosis': prognosis2.pk},)
        self.assertSetEqual({d['year'] for d in response.data},
                            set(range(1927, 1930)))


class TestPopulationEntryAPI(WriteOnlyWithCanEditBaseDataTest, TestPermissionsMixin,
                             TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "populationentries"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = PopulationEntryFactory()
        populationentry: PopulationEntry = cls.obj
        population = populationentry.population.pk
        area = populationentry.area.pk
        gender = populationentry.gender.pk
        age_group = populationentry.age_group.pk

        data = dict(population=population,
                    area=area,
                    gender=gender,
                    age_group=age_group,
                    value=faker.pyfloat(positive=True))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPopStatisticAPI(WriteOnlyWithCanEditBaseDataTest,
                          TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "popstatistics"
    factory = PopStatisticFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        popstatistic: PopStatistic = cls.obj
        year = popstatistic.year.year

        cls.post_data = dict(year=year)
        cls.put_data = dict(year=year)
        cls.patch_data = dict(year=year)


class TestPopStatEntryAPI(WriteOnlyWithCanEditBaseDataTest,
                          TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "popstatentries"
    factory = PopStatEntryFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        popstatentry: PopStatEntry = cls.obj
        popstatistic = popstatentry.popstatistic.pk
        area = popstatentry.area.pk

        data = dict(popstatistic=popstatistic, area=area,
                    immigration=faker.pyfloat(positive=True),
                    emigration=faker.pyfloat(positive=True),
                    births=faker.pyfloat(positive=True),
                    deaths=faker.pyfloat(positive=True))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
