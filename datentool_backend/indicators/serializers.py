from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from datentool_backend.utils.geometry_fields import GeometrySRIDField

from .models import (Mode, ModeVariant, Stop,
                     # ReachabilityMatrix,
                     Router, Indicator)


class ModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mode
        fields = ('id', 'name')


class ModeVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeVariant
        fields = ('id', 'mode', 'name', 'meta', 'is_default')


# class ReachabilityMatrixSerializer(serializers.ModelSerializer):
    # class Meta:
        #model = ReachabilityMatrix
        #fields = ('id', 'from_cell', 'to_cell', 'variant', 'minutes')

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
