import os
import pandas as pd
import logging

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation

from django.conf import settings

from rest_framework import serializers
from rest_framework.fields import FileField, IntegerField, BooleanField

from datentool_backend.indicators.models import (Stop, MatrixStopStop)
from datentool_backend.utils.processes import ProcessScope


class MatrixStopStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatrixStopStop
        fields = ('from_stop', 'to_stop', 'minutes')


class MatrixStopStopTemplateSerializer(serializers.Serializer):
    """Serializer for uploading MatrixStopStopTemplate"""
    excel_or_visum_file = FileField()
    variant = IntegerField()
    drop_constraints = BooleanField(default=False)
    scope = ProcessScope.ROUTING
    logger = logging.getLogger('routing')

    class Meta:
        model = MatrixStopStop
        fields = ('from_stop', 'to_stop', 'minutes')

    def create_template(self) -> bytes:
        columns = {'von': 'Von Haltestelle (Nr)',
                  'nach': 'Nach Haltestelle (Nr)',
                  'Minuten': 'Reisezeit in Minuten',
                  }
        df = pd.DataFrame(columns=pd.Index(columns.items()))
        fn = os.path.join(settings.MEDIA_ROOT, 'Reisezeitmatrix_Haltestelle_zu_Haltestelle.xlsx')
        sheetname = 'Reisezeit'
        with pd.ExcelWriter(fn, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheetname, freeze_panes=(2, 3))
            ws: Worksheet = writer.sheets.get(sheetname)

            dv = DataValidation(type="decimal",
                                operator="between",
                                formula1=0,
                                formula2=999999999,
                                allow_blank=True)

            dv.error ='Reisezeit muss größer oder gleich 0 Minuten sein'
            dv.errorTitle = 'Ungültige Reisezeit'
            ws.add_data_validation(dv)
            dv.add('D3:D999999')

            dv = DataValidation(type="whole",
                                operator="between",
                                formula1=0,
                                formula2=9999999,
                                allow_blank=False)

            dv.error ='Haltestellennummern müssen Ganzzahlen sein'
            dv.errorTitle = 'Ungültige Haltestellennummer'
            ws.add_data_validation(dv)
            dv.add('B3:C999999')

            ws.column_dimensions['A'] = ColumnDimension(ws, index='A', hidden=True)
            for col in 'BCD':
                ws.column_dimensions[col] = ColumnDimension(ws, index=col, width=30)

        content = open(fn, 'rb').read()
        return content

