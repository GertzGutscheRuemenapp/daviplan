from faker import Factory, Faker
from faker.generator import Generator
import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import Point
from .models import (SymbolForm, MapSymbols, LayerGroup, Layer,
                     WMSLayer, InternalWFSLayer, SourceTypes, Source,
                     AreaLevel, Area)
from ..user.factories import ProfileFactory


faker = Faker('de-DE')


class SymbolFormFactory(DjangoModelFactory):
    class Meta:
        model = SymbolForm

    name = faker.word()


class MapSymbolsFactory(DjangoModelFactory):
    class Meta:
        model = MapSymbols

    symbol = factory.SubFactory(SymbolFormFactory)
    fill_color = faker.color()
    stroke_color = faker.color()


class LayerGroupFactory(DjangoModelFactory):
    class Meta:
        model = LayerGroup
        django_get_or_create = ('order',)

    name = faker.word()
    order = faker.pyint(max_value=10)


class LayerFactory(DjangoModelFactory):
    class Meta:
        model = Layer
        django_get_or_create = ('order',)
    name = faker.word()
    group = factory.SubFactory(LayerGroupFactory)
    layer_name = faker.word()
    order = faker.pyint(max_value=10)


class WMSLayerFactory(LayerFactory):
    class Meta:
        model = WMSLayer
    url = faker.url()


class InternalWFSLayerFactory(LayerFactory):
    class Meta:
        model = InternalWFSLayer
    symbol = factory.SubFactory(MapSymbolsFactory)


class SourceFactory(DjangoModelFactory):
    class Meta:
        model = Source
    source_type = faker.random_element(SourceTypes)
    date = faker.date()
    id_field = faker.uuid4()
    url = faker.url()
    layer = faker.word()


class AreaLevelFactory(DjangoModelFactory):
    class Meta:
        model = AreaLevel
    name = faker.word()
    order = faker.pyint(max_value=10)
    source = factory.SubFactory(SourceFactory)
    layer = factory.SubFactory(InternalWFSLayerFactory)


class AreaFactory(DjangoModelFactory):
    class Meta:
        model = Area
    area_level = factory.SubFactory(AreaLevelFactory)
    geom = Point(faker.latlng())
    attributes = faker.json()

