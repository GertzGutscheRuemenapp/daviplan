import numpy as np
from django.test import TestCase
from .models import PrognosisEntry, Years
from .factories import (RasterCellFactory, AgeGroupFactory, AgeClassificationFactory,
                        GenderFactory,
                        DisaggPopRasterFactory, RasterPopulationCellFactory,
                        PrognosisEntryFactory, AreaFactory, PrognosisFactory,
                        PopStatEntryFactory)


class TestPopulation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.years = Years.objects.bulk_create([Years(year=y) for y in range(2010, 2015)],
                                              return_queryset=True)
        #cls.years = Years.objects.all()
        cls.cell = RasterCellFactory()
        cls.genders = [GenderFactory() for i in range(3)]
        cls.age_classification = AgeClassificationFactory()
        cls.disagg_popraster = DisaggPopRasterFactory(genders=cls.genders)

    def test_cell(self):
        cell = self.cell
        self.assertQuerysetEqual(
            self.disagg_popraster.genders.all(), self.genders, ordered=False)
        rp = RasterPopulationCellFactory()
        self.assertEqual(rp.cell.raster, rp.raster.raster)

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
