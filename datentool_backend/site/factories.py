import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import Polygon, MultiPolygon

from .models import ProjectSetting, SiteSetting, Year

from faker import Faker
faker = Faker('de-DE')


class YearFactory(DjangoModelFactory):
    class Meta:
        model = Year

    year = factory.Sequence(lambda n: int(faker.unique.year()))


class ProjectSettingFactory(DjangoModelFactory):
    class Meta:
        model = ProjectSetting

    project_area = MultiPolygon(
        Polygon(((0, 0), (10, 0), (10, 10), (0, 10), (0, 0)))
        )

def fakeword50(n=None):
    found = False
    while not found:
        word = faker.unique.word()
        if len(word) < 50:
            found = True
    return word


class SiteSettingFactory(DjangoModelFactory):
    class Meta:
        model = SiteSetting

    name = factory.Sequence(fakeword50)
    title = faker.word()
    contact_mail = faker.email()
    logo = faker.image_url('https://picsum.photos/788/861')
    primary_color = faker.hex_color()
    secondary_color = faker.hex_color()
    welcome_text = faker.text()

