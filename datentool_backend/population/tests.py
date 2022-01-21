import numpy as np

from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin,
                                        )


from .models import (PrognosisEntry,
                     Year,
                     PopulationRaster,
                     PopulationEntry,
                     PopStatistic,
                     PopStatEntry,
                     DisaggPopRaster,
                     Prognosis,
                     Population)
from .factories import (RasterCellFactory,
                        AgeGroupFactory,
                        GenderFactory,
                        PopulationFactory,
                        DisaggPopRasterFactory,
                        RasterCellPopulationFactory,
                        RasterCellPopulationAgeGenderFactory,
                        PrognosisEntryFactory,
                        AreaLevelFactory,
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
                                              #return_queryset=True,
                                              )
        cls.years = Year.objects.all()
        str(cls.years[0])
        cls.cell = RasterCellFactory()
        cls.genders = [GenderFactory() for i in range(3)]
        cls.disagg_popraster = DisaggPopRasterFactory(genders=cls.genders)

    def test_cell(self):
        self.assertQuerysetEqual(
            self.disagg_popraster.genders.all(), self.genders, ordered=False)
        rp = RasterCellPopulationAgeGenderFactory()
        self.assertEqual(rp.cell.raster, rp.disaggraster.popraster.raster)
        str(rp.cell)

    def test_prognosis(self):
        """Test the prognosis"""
        pe = list()
        area = AreaFactory()
        prognosis = PrognosisFactory(years=self.years, raster__genders=self.genders)
        agegroups = [AgeGroupFactory(), AgeGroupFactory(), AgeGroupFactory()]
        years = prognosis.years.all()
        genders = prognosis.raster.genders.all()
        for agegroup in agegroups:
            for year in years:
                for gender in genders:
                    pe.append(PrognosisEntryFactory.build(prognosis=prognosis,
                                                          year=year,
                                                          area=area,
                                                          agegroup=agegroup,
                                                          gender=gender))

        PrognosisEntry.objects.bulk_create(pe)
        pe_set = prognosis.prognosisentry_set.all()
        values = np.array(pe_set.values_list('value')).\
            reshape(len(agegroups), len(years), len(genders))

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


class TestDisaggPopRasterAPI(WriteOnlyWithCanEditBaseDataTest,
                             TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "disaggpoprasters"
    factory = DisaggPopRasterFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        disaggpopraster: DisaggPopRaster = cls.obj
        popraster = disaggpopraster.popraster.pk
        genders = list(disaggpopraster.genders.all().values_list(flat=True))

        data = dict(popraster=popraster, genders=genders)
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
        prognosis: Prognosis = cls.obj
        years = list(prognosis.years.all().values_list(flat=True))
        raster = prognosis.raster.pk

        data = dict(name=faker.word(), years=years, raster=raster,
                    is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPrognosisEntryAPI(WriteOnlyWithCanEditBaseDataTest,
                            TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "prognosisentries"
    factory = PrognosisEntryFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        prognosisentry: PrognosisEntry = cls.obj
        prognosis = prognosisentry.prognosis.pk
        year = prognosisentry.year.pk
        area = prognosisentry.area.pk
        agegroup = prognosisentry.agegroup.pk
        gender = prognosisentry.gender.pk

        data = dict(prognosis=prognosis, year=year, area=area, agegroup=agegroup,
                    gender=gender, value=faker.pyfloat(positive=True))
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
        area_level = population.area_level.pk
        year = population.year.pk
        genders = list(population.genders.all().values_list(flat=True))
        raster = population.raster.pk

        data = dict(area_level=area_level, year=year, genders=genders,
                    raster=raster)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPopulationEntryAPI(WriteOnlyWithCanEditBaseDataTest, TestPermissionsMixin,
                             TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "populationentries"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        area_level= AreaLevelFactory()
        cls.obj = PopulationEntryFactory(population__area_level=area_level,
                                          area__area_level=area_level)
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
