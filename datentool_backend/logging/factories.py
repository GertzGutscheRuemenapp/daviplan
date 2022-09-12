from faker import Faker
import factory
from .models import LogEntry
from factory.django import DjangoModelFactory

from ..user.factories import ProfileFactory
from ..infrastructure.factories import ServiceFactory, InfrastructureFactory
from ..area.factories import AreaLevelFactory

faker = Faker('de-DE')


class LogEntryFactory(DjangoModelFactory):
    user = factory.SubFactory(ProfileFactory)
    date = faker.date()
    text = faker.sentence()
    level = faker.word()
    room = faker.word()

    class Meta:
        model = LogEntry
