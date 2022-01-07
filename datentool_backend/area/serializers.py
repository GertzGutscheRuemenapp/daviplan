from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (MapSymbol, LayerGroup, WMSLayer,
                     InternalWFSLayer, Source, AreaLevel, Area)


class MapSymbolsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapSymbol
        fields =  ('symbol', 'fill_color', 'stroke_color')


class LayerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerGroup
        fields = ('id', 'name', 'order', 'external')


class WMSLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WMSLayer
        fields = ('id', 'name', 'group', 'layer_name', 'order', 'url',
                  'description')
        optional_fields = ('description', )


class InternalWFSLayerSerializer(serializers.ModelSerializer):
    symbol = MapSymbolsSerializer()

    class Meta:
        model = InternalWFSLayer
        fields = ('id', 'name', 'group', 'layer_name', 'order', 'symbol')
        read_only_fields = ('group', 'symbol')

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('id', 'source_type', 'date', 'id_field', 'url', 'layer')


class AreaLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaLevel
        fields = ('id', 'name', 'order', 'source', 'layer')


class AreaSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Area
        geo_field = 'geom'
        fields = ('id', 'area_level', 'attributes')
