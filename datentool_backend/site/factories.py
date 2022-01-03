import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import Polygon, MultiPolygon
from faker import Faker

from .models import ProjectSetting, BaseDataSetting, SiteSetting
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


#class SiteSettingFactory(DjangoModelFactory):
    #class Meta:
        #model = SiteSetting

    #url = faker.url()
    #name = faker.word()
    #title = faker.word()
    #contact_mail = faker.email()
    #logo = faker.image(null, 640, 480)
    #primary_color = faker.hexColor()
    #secondary_color = faker.hexColor()
    #welcome_text = faker.text()
