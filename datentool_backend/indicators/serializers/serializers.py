import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.protection import SheetProtection
from openpyxl.worksheet.worksheet import Worksheet, CellRange
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation
from django.conf import settings
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.fields import FileField

from openpyxl import Workbook
from openpyxl.writer.excel import save_workbook, save_virtual_workbook
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

    def create_template(self):
        columns = {'HstNr': 'wie in Reisezeitmatrix',
                  'HstName': 'Name der Haltestelle',
                  'Lon': 'Längengrad, in WGS84',
                  'Lat': 'Breitengrad, in WGS84',}
        df = pd.DataFrame(columns=pd.Index(columns.items()))
        fn = os.path.join(settings.MEDIA_ROOT, 'Haltestellen.xlsx')
        sheetname = 'Haltestellen'
        with pd.ExcelWriter(fn, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheetname, freeze_panes=(2, 2))
            ws: Worksheet = writer.sheets.get(sheetname)

            dv = DataValidation(type="decimal",
                                operator="between",
                                formula1=0,
                                formula2=90,
                                allow_blank=True)

            dv.error ='Koordinaten müssen in WGS84 angegeben werden und zwischen 0 und 90 liegen'
            dv.errorTitle = 'Ungültige Koordinaten'
            ws.add_data_validation(dv)
            dv.add('D3:E999999')

            dv = DataValidation(type="whole",
                                operator="between",
                                formula1=0,
                                formula2=9999999,
                                allow_blank=False)

            dv.error ='Haltestellennummern müssen Ganzzahlen sein'
            dv.errorTitle = 'Ungültige Haltestellennummer'
            ws.add_data_validation(dv)
            dv.add('B3:B999999')

            ws.column_dimensions['A'] = ColumnDimension(ws, index='A', hidden=True)
            for col in 'BCDE':
                ws.column_dimensions[col] = ColumnDimension(ws, index=col, width=30)

        content = open(fn, 'rb').read()
        return content


class UploadStopTemplateSerializer(serializers.Serializer):
    """"""
    excel_file = FileField()


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
