import numpy as np
from unittest import skip
from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        WriteOnlyWithAdminAccessTest)
from datentool_backend.area.tests import (_TestAPI, _TestPermissions)

from .models import (PrognosisEntry, Year, PopulationRaster, PopulationEntry,
                     PopStatistic, PopStatEntry, DisaggPopRaster,
                     Prognosis, Population)
from .factories import (YearFactory, RasterCellFactory, AgeGroupFactory,
                        GenderFactory, PopulationFactory, DisaggPopRasterFactory,
                        RasterCellPopulationAgeGenderFactory, PrognosisEntryFactory,
                        AreaFactory, PrognosisFactory, PopStatEntryFactory,
                        RasterFactory, PopulationRasterFactory,
                        PopulationEntryFactory, PopStatisticFactory)
from .constants import RegStatAgeGroup, RegStatAgeGroups

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
        cls.cell = RasterCellFactory()
        cls.genders = [GenderFactory() for i in range(3)]
        cls.disagg_popraster = DisaggPopRasterFactory(genders=cls.genders)

    def test_cell(self):
        cell = self.cell
        self.assertQuerysetEqual(
            self.disagg_popraster.genders.all(), self.genders, ordered=False)
        rp = RasterCellPopulationAgeGenderFactory()
        self.assertEqual(rp.cell.raster, rp.disaggraster.popraster.raster)

    #def test_age_group(self):
        #"""Test the age groups"""
        #from_age = 0
        #for ag in self.age_classification.agegroup_set.all():
            #self.assertEqual(ag.from_age, from_age)
            #self.assertLessEqual(ag.from_age, ag.to_age)
            #from_age = ag.to_age + 1
        #self.assertLessEqual(ag.to_age, 127)

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
        print(values)

    def test_popstatistic(self):
        ps = PopStatEntryFactory()
        print(ps.area.attributes)

    def test_population(self):
        pop = PopulationFactory(genders=self.genders)
        self.assertQuerysetEqual(
            pop.genders.all(), self.genders, ordered=False)


class TestYearAPI(WriteOnlyWithCanEditBaseDataTest,
                    _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "years"
    factory = YearFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.post_data = dict(year=1990)
        cls.put_data = dict(year=1995)
        cls.patch_data = dict(year=2000)


class TestRasterAPI(WriteOnlyWithCanEditBaseDataTest,
                    _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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
                              _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "populationrasters"
    factory = PopulationRasterFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        populationraster: PopulationRaster = cls.obj
        raster = populationraster.raster.pk
        year = populationraster.year.pk

        data = dict(name=faker.word(), raster=raster, year=year, default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestGenderAPI(WriteOnlyWithCanEditBaseDataTest,
                    _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "gender"
    factory = GenderFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.post_data = dict(name=faker.word())
        cls.put_data = dict(name=faker.word())
        cls.patch_data = dict(name=faker.word())



class TestAgeGroupAPI(WriteOnlyWithAdminAccessTest,
                      _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "agegroups"
    factory = AgeGroupFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(from_age=faker.pyint(max_value=127),
                    to_age=faker.pyint(max_value=127))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    @skip('only write access with admin access, not with can_edit_basedata')
    def test_can_edit_basedata(self):
        pass

    def test_admin_access(self):
        """write permission if user has admin_access"""
        super().admin_access()

    def test_default_agegroups(self):
        """test default agegroups"""
        response = self.get_check_200(self.url_key + '-list',
                                      data={'defaults': True, })
        print(response.data)
        assert(len(response.data) == len(RegStatAgeGroups.agegroups))

    def test_check_and_replace_agegroups(self):
        """check the agegroups"""
        # logout to see if check is not allowed
        self.client.logout()
        response = self.post(self.url_key + '-check')
        self.assert_http_401_unauthorized(response)

        # login and check that the current agegroups are not valid
        self.client.force_login(self.profile.user)

        response = self.get_check_200(self.url_key + '-list')
        current_agegroups = response.data

        response = self.post(self.url_key + '-check',
                             data=current_agegroups,
                             extra={'format': 'json'})
        self.assert_http_200_ok(response)
        self.assertEqual(response.data['valid'], False)

        # logout to see if check is not allowed
        self.client.logout()
        response = self.post(self.url_key + '-replace')
        self.assert_http_401_unauthorized(response)

        # login without can_edit_basedata is not allowed
        self.client.force_login(self.profile.user)
        response = self.post(self.url_key + '-replace')
        self.assert_http_403_forbidden(response)

        #  with can_edit_basedata it should work
        self.profile.can_edit_basedata = True
        self.profile.save()

        #  get the default agegroups
        response = self.get_check_200(self.url_key + '-list',
                                      data={'defaults': True, })
        default_agegroups = response.data


        #  post them to the replace route
        response = self.post(self.url_key + '-replace',
                             data=default_agegroups,
                             extra={'format': 'json'})
        self.assert_http_200_ok(response)
        assert(len(response.data) == len(RegStatAgeGroups.agegroups))

        response = self.get_check_200(self.url_key + '-list')
        current_agegroups = response.data

        #  now the check should work
        response = self.post(self.url_key + '-check',
                             data=current_agegroups,
                             extra={'format': 'json'})

        self.assert_http_200_ok(response)
        self.assertEqual(response.data['valid'], True)

        # change some agegroup definition
        pk1 = current_agegroups[-1]['id']
        pk2 = current_agegroups[-2]['id']

        self.profile.admin_access = True
        self.profile.save()
        response = self.patch(self.url_key + '-detail', pk=pk1,
                              data={'fromAge': 83, }, extra={'format': 'json'})
        self.assert_http_200_ok(response)
        response = self.patch(self.url_key + '-detail', pk=pk2,
                              data={'toAge': 82, }, extra={'format': 'json'})
        self.assert_http_200_ok(response)

        #  get the whole agegroups
        response = self.get_check_200(self.url_key + '-list')
        current_agegroups = response.data

        #  check if they are still valid
        response = self.post(self.url_key + '-check',
                             data=current_agegroups,
                             extra={'format': 'json'})

        #  they should fail now
        self.assert_http_200_ok(response)
        self.assertEqual(response.data['valid'], False)


class TestRegStatAgeGroup(TestCase):

    def test_repr_of_agegroups(self):
        """Test the representation of agegroups"""
        ag1 = RegStatAgeGroup(from_age=4, to_age=8)
        print(ag1.name)
        print(ag1.code)

    def test_compare_agegroups(self):
        """Test to compare agegroups"""
        ag1 = RegStatAgeGroup(from_age=4, to_age=8)
        ag2 = RegStatAgeGroup(from_age=9, to_age=12)
        ag3 = RegStatAgeGroup(from_age=9, to_age=12)
        assert ag2 == ag3
        assert ag1 != ag2
        assert ag1 != ag3


class TestDisaggPopRasterAPI(WriteOnlyWithCanEditBaseDataTest,
                             _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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
                       _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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
                            _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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
                        _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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


# class TestPopulationEntryAPI(WriteOnlyWithCanEditBaseDataTest, _TestAPI, BasicModelTest, APITestCase):
    #""""""
    #url_key = "populationentries"
    #factory = PopulationEntryFactory

    #@classmethod
    #def setUpTestData(cls):
        #super().setUpTestData()
        #populationentry: PopulationEntry = cls.obj
        #population = populationentry.population.pk
        #area = populationentry.area.pk
        #gender = populationentry.gender.pk

        #data = dict(population=population,
                    #area=area,
                    #gender=gender,
                    #age=faker.pyint(max_value=127),
                    #value=faker.pyfloat(positive=True))
        #cls.post_data = data
        #cls.put_data = data
        #cls.patch_data = data


class TestPopStatisticAPI(WriteOnlyWithCanEditBaseDataTest,
                          _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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
                          _TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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
