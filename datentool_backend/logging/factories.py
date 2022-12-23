import factory
from .models import LogEntry
from factory.django import DjangoModelFactory

from datentool_backend.user.factories import ProfileFactory

from faker import Faker
faker = Faker('de-DE')


class LogEntryFactory(DjangoModelFactory):
    user = factory.SubFactory(ProfileFactory)
    date = faker.date()
    text = faker.sentence()
    level = faker.word()
    room = faker.word()

    class Meta:
        model = LogEntry
