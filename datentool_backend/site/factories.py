import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import Polygon, MultiPolygon
from faker import Faker

from .models import ProjectSetting, BaseDataSetting
from datentool_backend.area.factories import AreaLevelFactory


faker = Faker('de-DE')

class ProjectSettingFactory(DjangoModelFactory):
    class Meta:
        model = ProjectSetting

    project_area = MultiPolygon(
        Polygon(((0, 0), (10, 0), (10, 10), (0, 10), (0, 0)))
        )
    start_year = 2000
    end_year = 2040


class BaseDataSettingFactory(DjangoModelFactory):
    class Meta:
        model = BaseDataSetting

    default_pop_area_level = factory.SubFactory(AreaLevelFactory)
