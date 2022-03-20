import os
from django.conf import settings
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from openpyxl import Workbook
from openpyxl.writer.excel import save_workbook, save_virtual_workbook
from tempfile import NamedTemporaryFile
from datentool_backend.utils.geometry_fields import GeometrySRIDField

from datentool_backend.indicators.models import (Stop, Router)
from datentool_backend.area.models import Area
from datentool_backend.population.models import RasterCell
from datentool_backend.infrastructure.models import Place


class StopSerializer(GeoFeatureModelSerializer):
    geom = GeometrySRIDField(srid=3857)

    class Meta:
        model = Stop
        geo_field = 'geom'
        fields = ('id', 'name')

    @classmethod
    def create_template(cls):
        wb = Workbook()
        ws = wb.active
        columns = {'A': 'wie in Reisezeitmatrix',
                  'B': 'Name der Haltestelle',
                  'C': 'Längengrad, in WGS84',
                  'D': 'Breitengrad, in WGS84',}
        #columns = {'HstNr': 'wie in Reisezeitmatrix',
                  #'HstName': 'Name der Haltestelle',
                  #'Lon': 'Längengrad, in WGS84',
                  #'Lat': 'Breitengrad, in WGS84',}
        ws.append(columns)

        fn = os.path.join(settings.MEDIA_ROOT, 'Haltestellen.xlsx')
        success = save_workbook(wb, fn)
        if not success:
            raise IOError(f'could not writer temporary excel-file to {fn}')

        content = open(fn, 'rb').read()
        return content


class IndicatorSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    title = serializers.CharField()
    result_type = serializers.SerializerMethodField('get_result_type')
    additional_parameters = serializers.SerializerMethodField('get_parameters')

    def get_result_type(self, obj):
        if obj.result_serializer:
            return obj.result_serializer.name.lower()
        return 'none'

    def get_parameters(self, obj):
        if not obj.params:
            return []
        return [p.serialize() for p in obj.params]


class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ('id', 'name', 'osm_file', 'tiff_file', 'gtfs_file',
                  'build_date', 'buffer')


class IndicatorAreaResultSerializer(serializers.ModelSerializer):
    label = serializers.CharField()
    value = serializers.FloatField()
    area_id = serializers.IntegerField(source='id')
    class Meta:
        model = Area
        fields = ('area_id', 'label', 'value')


class IndicatorRasterResultSerializer(serializers.ModelSerializer):
    cell_code = serializers.CharField()
    value = serializers.FloatField()
    class Meta:
        model = RasterCell
        fields = ('cell_code', 'value')


class IndicatorPlaceResultSerializer(serializers.ModelSerializer):
    place_id = serializers.IntegerField(source='id')
    value = serializers.FloatField()
    class Meta:
        model = Place
        fields = ('place_id', 'value')


class IndicatorPopulationSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    gender = serializers.IntegerField()
    agegroup = serializers.IntegerField()
    value = serializers.FloatField()
