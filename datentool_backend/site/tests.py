import io
import os

from test_plus import APITestCase
from django.contrib.gis.geos import Polygon, MultiPolygon
from rest_framework import status
from PIL import Image

from datentool_backend.api_test import (BasicModelSingletonTest,
                                        TestPermissionsMixin,
                                        BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        SingletonWriteOnlyWithAdminAccessTest,
                                        TestAPIMixin)
from datentool_backend.user.factories import ProfileFactory
from datentool_backend.site.factories import (ProjectSettingFactory,
                                              SiteSettingFactory, YearFactory)
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



class TestProjectSetting(SingletonWriteOnlyWithAdminAccessTest,
                         TestAPIMixin, BasicModelSingletonTest, APITestCase):
    """"""
    url_key = "projectsettings"
    factory = ProjectSettingFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        ewkt = 'SRID=4326;MULTIPOLYGON (\
((0 0, 0 2, 2 2, 2 0, 0 0)),\
 ((3 3, 3 7, 7 7, 7 3, 3 3), (4 4, 4 5, 5 5, 5 4, 4 4))\
)'

        geom = MultiPolygon.from_ewkt(ewkt)
        geom.transform(3857)
        ewkt_web_mercator = geom.ewkt

        cls.expected_put_data = dict(project_area=ewkt_web_mercator)

        cls.put_data = dict(from_year=2002,
                    to_year=2033,
                    project_area=ewkt
                    )


        # test if it is automatically transformed to wgs84 and tranformed to multipolygon
        ewkt_25832 = 'SRID=25832;POLYGON (\
(-505646.8995158707 0,-505028.1105357731 223833.1735327606,-280405.62793313444 222731.06606055034,-280882.93915922474 0,-505646.8995158707 0)\
)'

        cls.patch_data = dict(from_year=2002,
                    to_year=2033,
                    project_area=ewkt_25832,
                    )

        geom = Polygon.from_ewkt(ewkt_25832)
        geom = MultiPolygon(geom, srid=geom.srid)
        geom.transform(3857)
        ewkt_web_mercator = geom.ewkt

        cls.expected_patch_data = dict(project_area=ewkt_web_mercator)


class TestSiteSetting(TestAPIMixin, BasicModelSingletonTest, APITestCase):
    """"""
    url_key = "sitesettings"
    factory = SiteSettingFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        file = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)

        data = dict(name=faker.unique.word(), title=faker.word(),
                    contact_mail=faker.email(),
                    logo=file,
                    primary_color=faker.color(hue='blue'),
                    secondary_color=faker.color(hue='red'),
                    welcome_text=faker.text())
        cls.put_data = data
        cls.patch_data = data

    def test_put_patch(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        format_multipart = dict(format='multipart')
        # Permission: has admin_access
        profile = self.profile
        permission_admin = profile.admin_access

        profile.admin_access = True
        profile.save()

        # test get
        response = self.get_check_200(url, **kwargs)
        if 'id' in response.data:
            assert response.data['id'] == self.obj.pk

        # check status code for put
        logo = self.patch_data['logo']
        logo.seek(0)

        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=format_multipart)
        self.response_200(msg=response.content)
        assert response.status_code == status.HTTP_200_OK
        # check if values have changed
        response = self.get_check_200(url, **kwargs)

        logo = response.data.pop('logo')

        expected = self.put_data.copy()
        logo_file = expected.pop('logo')
        self.assertEqual(os.path.splitext(logo)[1], os.path.splitext(logo_file.name)[1])
        expected.update(self.expected_put_data)
        self.compare_data(response.data, expected)

        # check status code for patch
        logo = self.patch_data['logo']
        logo.seek(0)
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=format_multipart)
        self.response_200(msg=response.content)

        # check if name has changed
        response = self.get_check_200(url, **kwargs)
        logo = response.data.pop('logo')

        expected = self.patch_data.copy()
        logo_file = expected.pop('logo')
        self.assertEqual(os.path.splitext(logo)[1], os.path.splitext(logo_file.name)[1])
        expected.update(self.expected_patch_data)
        self.compare_data(response.data, expected)

        # Resetting admin_access permission
        profile.admin_access = permission_admin
        profile.save()

    def test_admin_access(self):
        """write permission if user has admin_access, check methods put, patch"""

        pr1 = ProfileFactory(admin_access=True)

        self.client.force_login(pr1.user)

        url = self.url_key + '-detail'
        kwargs = self.kwargs
        format_multipart = dict(format='multipart')

        # test get
        response = self.get_check_200(url, **kwargs)
        if 'id' in response.data:
            assert response.data['id'] == self.obj.pk

        # check status code for put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=format_multipart)
        self.response_200(msg=response.content)
        assert response.status_code == status.HTTP_200_OK
        # check if values have changed
        response = self.get_check_200(url, **kwargs)

        logo = response.data.pop('logo')

        expected = self.put_data.copy()
        logo_file = expected.pop('logo')
        self.assertEqual(os.path.splitext(logo)[1], os.path.splitext(logo_file.name)[1])
        expected.update(self.expected_put_data)
        self.compare_data(response.data, expected)

        # check status code for patch
        logo = self.patch_data['logo']
        logo.seek(0)
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=format_multipart)
        self.response_200(msg=response.content)

        # check if name has changed
        response = self.get_check_200(url, **kwargs)
        logo = response.data.pop('logo')

        expected = self.patch_data.copy()
        logo_file = expected.pop('logo')
        self.assertEqual(os.path.splitext(logo)[1], os.path.splitext(logo_file.name)[1])
        expected.update(self.expected_patch_data)
        self.compare_data(response.data, expected)

        self.client.logout()
        self.client.force_login(self.profile.user)

        url = self.url_key + '-detail'
        kwargs = self.kwargs
        format_multipart = dict(format='multipart')

        # test get
        response = self.get_check_200(url, **kwargs)
        if 'id' in response.data:
            assert response.data['id'] == self.obj.pk

        # check status code for put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=format_multipart)
        self.response_403(msg=response.content)

        # check status code for patch
        logo = self.patch_data['logo']
        logo.seek(0)
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=format_multipart)
        self.response_403(msg=response.content)

