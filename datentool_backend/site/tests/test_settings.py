import io
import os

from test_plus import APITestCase
from django.contrib.gis.geos import Polygon, MultiPolygon
from rest_framework import status
from PIL import Image

from datentool_backend.api_test import (BasicModelSingletonTest,
                                        SingletonWriteOnlyWithAdminAccessTest,
                                        TestAPIMixin)
from datentool_backend.user.factories import ProfileFactory
from datentool_backend.site.factories import (ProjectSettingFactory,
                                              SiteSettingFactory)

from faker import Faker
faker = Faker('de-DE')


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

        data = self.put_data.copy()
        data['sync'] = True

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

