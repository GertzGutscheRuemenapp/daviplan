from faker import Faker
import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import MultiPolygon, Polygon
from .models import (MapSymbol, LayerGroup, Layer,
                     WMSLayer, InternalWFSLayer, SourceTypes, Source,
                     AreaLevel, Area)


faker = Faker('de-DE')


class MapSymbolsFactory(DjangoModelFactory):
    class Meta:
        model = MapSymbol

    # ToDo: random choice?
    symbol = MapSymbol.Symbol.SQUARE
    fill_color = faker.color()
    stroke_color = faker.color()


class LayerGroupFactory(DjangoModelFactory):
    class Meta:
        model = LayerGroup

    name = faker.word()
    order = factory.Sequence(lambda n: faker.pyint(max_value=10))


class LayerFactory(DjangoModelFactory):
    class Meta:
        model = Layer
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
    order = faker.unique.pyint(max_value=10)
    source = factory.SubFactory(SourceFactory)
    layer = factory.SubFactory(InternalWFSLayerFactory)


class AreaFactory(DjangoModelFactory):
    class Meta:
        model = Area
    area_level = factory.SubFactory(AreaLevelFactory)
    geom = MultiPolygon(Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0))),
                        Polygon(((20, 20), (20, 30), (30, 30), (30, 20), (20, 20))))
    attributes = faker.json(data_columns={'gen': 'word',
                                          'inhabitants': 'pyint',},
                            num_rows=1)

