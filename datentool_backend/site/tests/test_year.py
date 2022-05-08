from test_plus import APITestCase
from rest_framework import status

from datentool_backend.api_test import (TestPermissionsMixin,
                                        BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin)
from datentool_backend.user.factories import ProfileFactory
from datentool_backend.site.factories import YearFactory
from datentool_backend.site.models import Year

from faker import Faker
faker = Faker('de-DE')


class TestYearAPI(WriteOnlyWithCanEditBaseDataTest,
                  TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "years"
    factory = YearFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.post_data = dict(year=1990)
        cls.put_data = dict(year=1995)
        cls.patch_data = dict(year=2000, is_default=True)

    def test_create_years(self):
        """test setting years"""
        self.profile.can_edit_basedata = True
        self.profile.save()
        url = 'years-set-range'

        # test min year error
        res = self.post(url, data={'from_year': Year.MIN_YEAR - 1,
                                   'to_year': Year.MIN_YEAR + 3},
                        extra={'format': 'json'})
        self.assert_http_400_bad_request(res)

        # test from > to error
        res = self.post(url, data={'from_year': Year.MIN_YEAR + 10,
                                   'to_year': Year.MIN_YEAR + 1},
                        extra={'format': 'json'})
        self.assert_http_400_bad_request(res)

        from_year, to_year = Year.MIN_YEAR, Year.MIN_YEAR + 20
        res = self.post(url, data={'from_year': from_year, 'to_year': to_year},
                        extra={'format': 'json'})
        self.assert_http_201_created(res)
        res_years = [r['year'] for r in res.data]
        qs = Year.objects.values_list('year', flat=True)
        expected = list(range(from_year, to_year + 1))
        self.assertQuerysetEqual(qs, expected, ordered=False)
        self.assertQuerysetEqual(res_years, expected, ordered=False)

        res = self.post(url, data={'from_year': '2130', 'to_year': 2140,},
                        extra={'format': 'json'})
        self.assert_http_201_created(res)
        res_years = [r['year'] for r in res.data]
        qs = Year.objects.values_list('year', flat=True)
        expected = list(range(2130, 2141))
        self.assertQuerysetEqual(qs, expected, ordered=False)
        self.assertQuerysetEqual(res_years, expected, ordered=False)

        res = self.post(url, data={'from_year': '2130.2', 'to_year': 2140,},
                                 extra={'format': 'json'})
        self.assert_http_400_bad_request(res)

    def test_query_params(self):
        """test the query params"""
        Year.objects.all().delete()
        for y in range(2020, 2050):
            year = Year.objects.create(year=y, is_prognosis=not(y % 5))
        url = 'years-list'
        # all years
        res = self.get_check_200(url,
                                 extra={'format': 'json'})
        self.assertListEqual([r['year'] for r in res.data],
                             list(range(2020, 2050, 1)))
        # prognosis years
        res = self.get_check_200(url,
                                 data={'is_prognosis': True,},
                                 extra={'format': 'json'})
        self.assertListEqual([r['year'] for r in res.data],
                             list(range(2020, 2050, 5)))
