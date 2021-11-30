import numpy as np
from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI

from .models import (PrognosisEntry, Year, PopulationRaster, AgeGroup,
                     PopulationEntry, PopStatistic, PopStatEntry, DisaggPopRaster,
                     Prognosis, Population)
from .factories import (RasterCellFactory, AgeGroupFactory, AgeClassificationFactory,
                        GenderFactory, PopulationFactory, DisaggPopRasterFactory,
                        RasterCellPopulationAgeGenderFactory, PrognosisEntryFactory,
                        AreaFactory, PrognosisFactory, PopStatEntryFactory,
                        RasterFactory, PopulationRasterFactory,
                        PopulationEntryFactory, PopStatisticFactory)

from faker import Faker

faker = Faker('de-DE')


class TestPopulation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.years = Year.objects.bulk_create([Year(year=y) for y in range(2010, 2015)],
                                              return_queryset=True)
        #cls.years = Year.objects.all()
        cls.cell = RasterCellFactory()
        cls.genders = [GenderFactory() for i in range(3)]
        cls.age_classification = AgeClassificationFactory()
        cls.disagg_popraster = DisaggPopRasterFactory(genders=cls.genders)

    def test_cell(self):
        cell = self.cell
        self.assertQuerysetEqual(
            self.disagg_popraster.genders.all(), self.genders, ordered=False)
        rp = RasterCellPopulationAgeGenderFactory()
        self.assertEqual(rp.cell.raster, rp.disaggraster.popraster.raster)

    def test_age_group(self):
        """Test the age groups"""
        from_age = 0
        for ag in self.age_classification.agegroup_set.all():
            self.assertEqual(ag.from_age, from_age)
            self.assertLessEqual(ag.from_age, ag.to_age)
            from_age = ag.to_age + 1
        self.assertLessEqual(ag.to_age, 127)

    def test_prognosis(self):
        """Test the prognosis"""
        pe = list()
        area = AreaFactory()
        prognosis = PrognosisFactory(years=self.years, raster__genders=self.genders)
        years = prognosis.years.all()
        genders = prognosis.raster.genders.all()
        agegroups = prognosis.age_classification.agegroup_set.all()
        for year in years:
            for gender in genders:
                for ag in agegroups:
                    pe.append(PrognosisEntryFactory.build(prognosis=prognosis,
                                                          year=year,
                                                          area=area,
                                                          gender=gender,
                                                          agegroup=ag))

        PrognosisEntry.objects.bulk_create(pe)
        pe_set = prognosis.prognosisentry_set.all()
        values = np.array(pe_set.values_list('value')).\
            reshape(len(years), len(genders), len(agegroups))
        print(values)

    def test_popstatistic(self):
        ps = PopStatEntryFactory()
        print(ps.area.attributes)

    def test_population(self):
        pop = PopulationFactory(genders=self.genders)
        self.assertQuerysetEqual(
            pop.genders.all(), self.genders, ordered=False)


class TestRasterAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "rasters"
    factory = RasterFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_data = dict(name=faker.word())
        cls.put_data = dict(name=faker.word())
        cls.patch_data = dict(name=faker.word())


class TestPopulationRasterAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "populationrasters"
    factory = PopulationRasterFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        populationraster: PopulationRaster = cls.obj
        raster = populationraster.raster.pk
        year = populationraster.year.pk

        data = dict(name=faker.word(), raster=raster, year=year, default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestGenderAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "gender"
    factory = GenderFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_data = dict(name=faker.word())
        cls.put_data = dict(name=faker.word())
        cls.patch_data = dict(name=faker.word())


#class TestAgeClassificationAPI(_TestAPI, BasicModelTest, APITestCase):
    #""""""
    #url_key = "ageclassifications"
    #factory = AgeClassificationFactory

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()

        #cls.post_data = dict(name=faker.word())
        #cls.put_data = dict(name=faker.word())
        #cls.patch_data = dict(name=faker.word())


class TestAgeGroupAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "agegroups"
    factory = AgeGroupFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        agegroup: AgeGroup = cls.obj
        classification = agegroup.classification.pk

        data = dict(classification=classification,
                    from_age=faker.pyint(max_value=127),
                    to_age=faker.pyint(max_value=127))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestDisaggPopRasterAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "disaggpoprasters"
    factory = DisaggPopRasterFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disaggpopraster: DisaggPopRaster = cls.obj
        popraster = disaggpopraster.popraster.pk
        genders = list(disaggpopraster.genders.all().values_list(flat=True))

        data = dict(popraster=popraster, genders=genders)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPrognosisAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "prognoses"
    factory = PrognosisFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prognosis: Prognosis = cls.obj
        years = list(prognosis.years.all().values_list(flat=True))
        raster = prognosis.raster.pk
        age_classification = prognosis.age_classification.pk

        data = dict(name=faker.word(), years=years, raster=raster,
                    age_classification=age_classification, is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPrognosisEntryAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "prognosisentries"
    factory = PrognosisEntryFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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


class TestPopulationAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "populations"
    factory = PopulationFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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


#class TestPopulationEntryAPI(_TestAPI, BasicModelTest, APITestCase):
    #""""""
    #url_key = "populationentries"
    #factory = PopulationEntryFactory

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()
        #populationentry: PopulationEntry = cls.obj
        #population = populationentry.population.pk
        #area = populationentry.area.pk
        #gender = populationentry.gender.pk

        #data = dict(population=population, area=area, gender=gender,
                    #age=faker.pyint(max_value=127), value=faker.pyfloat(positive=True))
        #cls.post_data = data
        #cls.put_data = data
        #cls.patch_data = data


class TestPopStatisticAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "popstatistics"
    factory = PopStatisticFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        popstatistic: PopStatistic = cls.obj
        year = popstatistic.year.pk

        cls.post_data = dict(year=year)
        cls.put_data = dict(year=year)
        cls.patch_data = dict(year=year)


class TestPopStatEntryAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "popstatentries"
    factory = PopStatEntryFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        popstatentry: PopStatEntry = cls.obj
        popstatistic = popstatentry.popstatistic.pk
        area = popstatentry.area.pk

        data = dict(popstatistic=popstatistic, area=area,
                    age=faker.pyint(max_value=127),
                    immigration=faker.pyfloat(positive=True),
                    emigration=faker.pyfloat(positive=True),
                    births=faker.pyfloat(positive=True),
                    deaths=faker.pyfloat(positive=True))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
