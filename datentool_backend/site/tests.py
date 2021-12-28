from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon, MultiPolygon
from collections import OrderedDict
from unittest import skip
from datentool_backend.api_test import BasicModelSingletonTest
from datentool_backend.area.tests import _TestAPI

from datentool_backend.site.factories import (ProjectSettingFactory, BaseDataSettingFactory)
from datentool_backend.site.models import ProjectSetting, BaseDataSetting
from datentool_backend.area.factories import AreaLevelFactory

from faker import Faker
faker = Faker('de-DE')


class TestBaseDataSetting(BasicModelSingletonTest, APITestCase):

    url_key = "basedatasettings"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area_level1 = AreaLevelFactory(order=2)
        cls.area_level2 = AreaLevelFactory(order=3)
        cls.obj = BaseDataSettingFactory(default_pop_area_level=cls.area_level1)


        data = dict(default_pop_area_level=cls.area_level2.pk)

        cls.put_data = data
        cls.patch_data = data


class TestProjectSetting(_TestAPI, BasicModelSingletonTest, APITestCase):
    """"""
    url_key = "projectsettings"
    factory = ProjectSettingFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        ewkt = 'SRID=4326;MULTIPOLYGON (\
((0 0, 0 2, 2 2, 2 0, 0 0)),\
 ((3 3, 3 7, 7 7, 7 3, 3 3), (4 4, 4 5, 5 5, 5 4, 4 4))\
)'


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
        geom.transform(4326)
        ewkt_wgs84 = geom.ewkt

        cls.expected_patch_data = dict(project_area=ewkt_wgs84)

    def test_admin_access(self):
        """write permission if user has admin_access, check methods put, patch"""
        profile = self.profile
        permission_admin = profile.admin_access

        # Testprofile, with admin_access
        profile.admin_access = True
        profile.save()

        self.test_put_patch()

        # Testprofile, without admin_access
        profile.admin_access = False
        profile.save()

        # test get, put, patch
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        # test get
        response = self.get(url, **kwargs)
        self.response_200(msg=response.content)
        # test put
        response = self.put(url, **kwargs,
                                data=self.put_data,
                                extra=formatjson)
        self.response_403(msg=response.content)

        # check status code for patch
        response = self.patch(url, **kwargs,
                                  data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

        profile.admin_access = permission_admin
        profile.save()


#class TestSiteSetting(_TestAPI, BasicModelSingletonTest, APITestCase):
    #""""""
    #url_key = "sitesettings"
    #factory = SiteSettingFactory