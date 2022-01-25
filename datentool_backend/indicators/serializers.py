from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from datentool_backend.utils.geometry_fields import GeometrySRIDField

from .models import (Stop, Router, Indicator)
from datentool_backend.area.models import Area
from datentool_backend.area.serializers import AreaSerializer


class StopSerializer(GeoFeatureModelSerializer):
    geom = GeometrySRIDField(srid=3857)

    class Meta:
        model = Stop
        geo_field = 'geom'
        fields = ('id', 'name')


class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ('id', 'name', 'osm_file', 'tiff_file', 'gtfs_file',
                  'build_date', 'buffer')


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = ('id', 'indicator_type', 'name', 'parameters', 'service')


class AreaIndicatorSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    value = serializers.FloatField()
    class Meta:
        model = Area
        fields = ('id', 'name', 'value')
