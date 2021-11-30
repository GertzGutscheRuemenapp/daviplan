from rest_framework import serializers

from .models import (Mode, ModeVariant, ReachabilityMatrix, Router, Indicator)


class ModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mode
        fields = ('id', 'name')


class ModeVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeVariant
        fields = ('id', 'mode', 'name', 'meta', 'is_default')


class ReachabilityMatrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReachabilityMatrix
        fields = ('id', 'from_cell', 'to_cell', 'variant', 'minutes')


class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ('id', 'name', 'osm_file', 'tiff_file', 'gtfs_file',
                  'build_date', 'buffer')


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = ('id', 'indicator_type', 'name', 'parameters', 'service')