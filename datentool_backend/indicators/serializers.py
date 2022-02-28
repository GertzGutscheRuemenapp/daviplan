from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from datentool_backend.utils.geometry_fields import GeometrySRIDField

from .models import (Stop, Router)
from datentool_backend.area.models import Area
from datentool_backend.user.models import Service


class StopSerializer(GeoFeatureModelSerializer):
    geom = GeometrySRIDField(srid=3857)

    class Meta:
        model = Stop
        geo_field = 'geom'
        fields = ('id', 'name')


class IndicatorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    description = serializers.CharField()
    title = serializers.CharField()
    detailed_title = serializers.CharField()
    class Meta:
        model = Service
        fields = ('id', 'description', 'title', 'detailed_title')


class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ('id', 'name', 'osm_file', 'tiff_file', 'gtfs_file',
                  'build_date', 'buffer')


class AreaIndicatorResponseSerializer(serializers.ModelSerializer):
    label = serializers.CharField()
    value = serializers.FloatField()
    area_id = serializers.IntegerField(source='id')
    class Meta:
        model = Area
        fields = ('area_id', 'label', 'value')


class PopulationIndicatorSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    gender = serializers.IntegerField()
    agegroup = serializers.IntegerField()
    value = serializers.FloatField()
