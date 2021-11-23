from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (Year, Raster, PopulationRaster, RasterCell)


class YearSerializer(serializers.ModelSerializer):
    model = Year
    fields = ('id', 'year')


class RasterSerializer(serializers.ModelSerializer):
    model = Raster
    fields = ('id', 'name')


class PopulationRasterSerializer(serializers.ModelSerializer):
    model = PopulationRaster
    fields = ('id', 'name', 'raster', 'year', 'default')


class RasterCellSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = RasterCell
        geo_field = 'point', 'poly'
        fields = ('id', 'raster', 'cellcode')
