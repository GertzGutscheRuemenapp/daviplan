import os
import numpy as np
import pandas as pd

from unittest import skip, skipIf
from unittest.mock import Mock, patch

from cryptography.fernet import Fernet

from django.conf import settings
from test_plus import APITestCase

from datentool_backend.utils.test_utils import no_connection
from datentool_backend.utils.regionalstatistik import Regionalstatistik
from datentool_backend.api_test import LoginTestCase
from datentool_backend.site.models import SiteSetting
from datentool_backend.utils.crypto import encrypt

from datentool_backend.site.factories import YearFactory
from datentool_backend.population.models import (Year,
                                                 PopulationEntry,
                                                 PopStatEntry)
from datentool_backend.population.factories import (
    AgeGroupFactory,
    GenderFactory,
    AreaFactory,
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


class TestRegionalstatistikAPI(LoginTestCase, APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.admin_access = True
        cls.profile.save()

        settings.ENCRYPT_KEY = Fernet.generate_key().decode('utf-8')

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

        self.pull_and_compare_population()
        popstatentries = self.pull_and_compare_popstatistics()
        self.compare_popstatistics_for_arealevel(popstatentries)

    def compare_popstatistics_for_arealevel(self, popstatentries: pd.DataFrame):
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

    def pull_and_compare_popstatistics(self) -> pd.DataFrame:
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
        return popstatentries

    def pull_and_compare_population(self):
        res = self.post('populations-pull-regionalstatistik',
                        data={'drop_constraints': False, },
                        extra={'format': 'json'})
        self.assert_http_202_accepted(res)
        popentries = pd.DataFrame(PopulationEntry.objects.values())

        actual = popentries.groupby(['area_id', 'population_id']).sum()['value']
        target = [211713, 212958, 214420, 311, 305, 315, 349, 335, 354]
        self.assertListEqual(list(actual), target)


    @skipIf(no_connection(Regionalstatistik.TEST_URL),
            'No Connection to Regionalstatistik API available')
    def test_unmocked(self):
        """Test the real Regionalstatistik-Api, if a connection is available"""
        site_settings: SiteSetting = SiteSetting.load()
        site_settings.regionalstatistik_user = os.environ.get('REGIONALSTATISTIK_USER',
                                                              'Testuser')

        ## check that without password login fails
        #site_settings.save()
        #res = self.post('populations-pull-regionalstatistik',
                        #data={'drop_constraints': False, },
                        #extra={'format': 'json'})

        #msg = '''Ein Fehler ist aufgetreten. (Bitte prüfen und korrigieren Sie Ihren Nutzernamen \nbzw. das Passwort.)'''
        #self.assert_http_406_not_acceptable(res, msg=msg)

        # set the password and try again
        pwd = os.environ.get('REGIONALSTATISTIK_PWD', 'Testpasswd')
        site_settings.regionalstatistik_password = encrypt(pwd)
        site_settings.save()

        self.pull_and_compare_population()
        popstatentries = self.pull_and_compare_popstatistics()
        self.compare_popstatistics_for_arealevel(popstatentries)

    def test_permissions(self):
        self.profile.admin_access = False
        self.profile.can_edit_basedata = False
        self.profile.save()

        res = self.post('popstatistics-pull-regionalstatistik',
                        extra={'format': 'json'})

        self.assert_http_403_forbidden(res)
