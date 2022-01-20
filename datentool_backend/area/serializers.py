from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from datentool_backend.utils.geometry_fields import MultiPolygonGeometrySRIDField

from .models import (MapSymbol, LayerGroup, WMSLayer,
                     Source, AreaLevel, Area)


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
                  'description', 'active')
        optional_fields = ('description', 'active')


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('id', 'source_type', 'date', 'id_field', 'url', 'layer')


class AreaLevelSerializer(serializers.ModelSerializer):
    source = SourceSerializer(allow_null=True, required=False)
    class Meta:
        model = AreaLevel
        fields = ('id', 'name', 'order', 'source', 'layer')


class AreaSerializer(GeoFeatureModelSerializer):
    geom = MultiPolygonGeometrySRIDField(srid=3857)
    class Meta:
        model = Area
        geo_field = 'geom'
        fields = ('id', 'area_level', 'attributes')
