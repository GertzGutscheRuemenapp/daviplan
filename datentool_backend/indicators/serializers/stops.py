import os
import pandas as pd
import logging

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation

from rest_framework import serializers
from rest_framework.fields import FileField, BooleanField

from django.conf import settings

from datentool_backend.utils.geometry_fields import GeometrySRIDField
from datentool_backend.indicators.models import Stop
from datentool_backend.utils.processes import ProcessScope


class StopSerializer(serializers.ModelSerializer):
    geom = GeometrySRIDField(srid=3857)

    class Meta:
        model = Stop
        fields = ('id', 'name', 'geom')


class StopTemplateSerializer(serializers.Serializer):
    """Serializer for uploading StopTemplate"""
    excel_file = FileField()
    drop_constraints = BooleanField(default=False,
                                    label='temporarily delete constraints and indices',
                                    help_text='Set to False in unittests')
    scope = ProcessScope.ROUTING
    logger = logging.getLogger('routing')

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
