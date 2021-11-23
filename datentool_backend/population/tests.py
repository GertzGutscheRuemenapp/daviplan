import numpy as np
from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI

from .models import PrognosisEntry, Year
from .factories import (RasterCellFactory, AgeGroupFactory, AgeClassificationFactory,
                        GenderFactory, PopulationFactory,
                        DisaggPopRasterFactory, RasterCellPopulationAgeGenderFactory,
                        PrognosisEntryFactory, AreaFactory, PrognosisFactory,
                        PopStatEntryFactory, YearFactory)

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


#class TestYearAPI(_TestAPI, BasicModelTest, APITestCase):
    #""""""
    #url_key = "years"
    #factory = YearFactory

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()

        #cls.post_data = dict(year=faker.unique.year())
        #cls.put_data = dict(year=faker.unique.year())
        #cls.patch_data = dict(year=faker.unique.year())
