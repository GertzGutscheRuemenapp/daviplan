from faker import Faker
import factory
from factory.django import DjangoModelFactory, mute_signals
from django.db.models.signals import post_save
from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog, LogEntry)

from ..user.factories import ProfileFactory
from ..infrastructure.factories import ServiceFactory, InfrastructureFactory
from ..area.factories import AreaLevelFactory


faker = Faker('de-DE')


@mute_signals(post_save)
class LogEntryFactory(DjangoModelFactory):

    user = factory.SubFactory(ProfileFactory)
    date = faker.date()
    text = faker.sentence()


class CapacityUploadLogFactory(LogEntryFactory):
    class Meta:
        model = CapacityUploadLog

    service = factory.SubFactory(ServiceFactory)


class PlaceUploadLogFactory(LogEntryFactory):
    class Meta:
        model = PlaceUploadLog

    infrastructure = factory.SubFactory(InfrastructureFactory)


class AreaUploadLogFactory(LogEntryFactory):
    class Meta:
        model = AreaUploadLog

    level = factory.SubFactory(AreaLevelFactory)

