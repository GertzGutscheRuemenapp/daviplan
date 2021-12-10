from django.test import TestCase
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon
from collections import OrderedDict

from datentool_backend.api_test import BasicModelSingletonTest
from datentool_backend.area.tests import _TestAPI

from datentool_backend.site.factories import ProjectSettingFactory, BaseDataSettingFactory
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

        data = dict(from_year=2002,
                    to_year=2033,
                    project_area=ewkt
                    )

        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
