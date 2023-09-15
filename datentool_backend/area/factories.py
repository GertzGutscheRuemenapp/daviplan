from faker import Faker
import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos import MultiPolygon, Polygon
from .models import (MapSymbol, LayerGroup, Layer,
                     WMSLayer, SourceTypes, Source,
                     AreaLevel, Area, AreaField,
                     FClass, FieldType, FieldTypes,
                     )


faker = Faker('de-DE')


class MapSymbolFactory(DjangoModelFactory):
    class Meta:
        model = MapSymbol

    symbol = faker.random_element(MapSymbol.Symbol)
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


class SourceFactory(DjangoModelFactory):
    class Meta:
        model = Source
    source_type = faker.random_element(SourceTypes)
    date = faker.date()
    url = faker.url()
    layer = faker.word()


class AreaLevelFactory(DjangoModelFactory):
    class Meta:
        model = AreaLevel
    name = factory.Sequence(lambda n: faker.unique.word())
    order = faker.unique.pyint(max_value=10)
    symbol = factory.SubFactory(MapSymbolFactory)
    source = factory.SubFactory(SourceFactory)
    is_preset = False
    is_active = True


class AreaFactory(DjangoModelFactory):
    class Meta:
        model = Area
    area_level = factory.SubFactory(AreaLevelFactory)
    geom = MultiPolygon(Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0))),
                        Polygon(((20, 20), (20, 30), (30, 30), (30, 20), (20, 20))),
                        srid=4326).transform(3857, clone=True)


class FieldTypeFactory(DjangoModelFactory):
    """a generic field type"""
    class Meta:
        model = FieldType

    ftype = faker.random_element(FieldTypes)
    name = factory.Sequence(lambda n: faker.unique.word())


class FClassFactory(DjangoModelFactory):
    """a class in a classification"""
    class Meta:
        model = FClass

    ftype = factory.SubFactory(FieldTypeFactory, ftype=FieldTypes.CLASSIFICATION)
    order = factory.Sequence(lambda n: faker.unique.pyint(max_value=100))
    value = factory.Sequence(lambda n: faker.unique.word())


class AreaFieldFactory(DjangoModelFactory):
    """area field factory"""
    class Meta:
        model = AreaField

    name = faker.unique.word()
    area_level = factory.SubFactory(AreaLevelFactory)
    field_type = factory.SubFactory(FieldTypeFactory)
