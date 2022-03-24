import os
import pandas as pd

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.fields import FileField, BooleanField

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.files import File

from datentool_backend.utils.geometry_fields import GeometrySRIDField
from datentool_backend.indicators.models import Stop


class StopSerializer(GeoFeatureModelSerializer):
    geom = GeometrySRIDField(srid=3857)

    class Meta:
        model = Stop
        geo_field = 'geom'
        fields = ('id', 'name')


class StopTemplateSerializer(serializers.Serializer):
    """Serializer for uploading StopTemplate"""
    excel_file = FileField()
    drop_constraints = BooleanField(default=True,
                                    label='temporarily delete constraints and indices',
                                    help_text='Set to False in unittests')

    def create_template(self) -> bytes:
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

    def read_excel_file(self, request) -> pd.DataFrame:
        """read excelfile and return a dataframe"""
        excel_file = request.FILES['excel_file']

        df = pd.read_excel(excel_file.file,
                           sheet_name='Haltestellen',
                           skiprows=[1])

        # assert the stopnumers are unique
        assert df['HstNr'].is_unique, 'Haltestellennummer ist nicht eindeutig'

        # create points out of Lat/Lon and transform them to WebMercator
        points = [Point(stop['Lon'], stop['Lat'], srid=4326).transform(3857, clone=True)
                  for i, stop in df.iterrows()]

        df2 = pd.DataFrame({'id': df['HstNr'],
                            'name': df['HstName'],
                            'geom': points,})
        return df2
