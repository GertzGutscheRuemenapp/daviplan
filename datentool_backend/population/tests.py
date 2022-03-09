import numpy as np

from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin,
                                        )


from .models import (Year,
                     PopulationRaster,
                     PopulationEntry,
                     PopStatistic,
                     PopStatEntry,
                     Prognosis,
                     Population)
from .factories import (RasterCellFactory,
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
                        PopStatisticFactory)

from faker import Faker

faker = Faker('de-DE')


class TestPopulation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.years = Year.objects.bulk_create([Year(year=y)
                                              for y in range(2010, 2015)],
                                              )
        cls.years = Year.objects.all()
        str(cls.years[0])
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

    def test_popstatistic(self):
        ps = PopStatEntryFactory()

    def test_population(self):
        pop = PopulationFactory(genders=self.genders)
        self.assertQuerysetEqual(
            pop.genders.all(), self.genders, ordered=False)

    def test_raster_population(self):
        rcp = RasterCellPopulationFactory()
        print(rcp)


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
        year = populationraster.year.pk

        data = dict(name=faker.word(), raster=raster, year=year, default=faker.pybool())
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
                                      data={'with_population': 1},)
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
        year = popstatistic.year.pk

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
