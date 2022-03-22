import os
import pandas as pd

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation

from rest_framework import serializers
from rest_framework.fields import FileField, IntegerField, BooleanField

from django.conf import settings
from django.core.files import File

from django.db import connection
from datentool_backend.utils.dict_cursor import dictfetchall

from datentool_backend.indicators.models import (Stop,
                                                 MatrixStopStop,
                                                 MatrixCellPlace,
                                                 )
from datentool_backend.infrastructure.models import Place
from datentool_backend.population.models import RasterCell, RasterCellPopulation


class MatrixStopStopSerializer(serializers.Serializer):

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


class UploadMatrixStopStopTemplateSerializer(serializers.Serializer):
    """Serializer for uploading MatrixStopStopTemplate"""
    excel_file = FileField()
    variant = IntegerField()
    drop_constraints = BooleanField(default=True)

    def read_excel_file(self, request) -> pd.DataFrame:
        """read excelfile and return a dataframe"""
        excel_file = request.FILES['excel_file']

        df = pd.read_excel(excel_file.file,
                           sheet_name='Reisezeit',
                           skiprows=[1])

        # assert the stopnumbers are in stops
        cols = ['id', 'name']
        df_stops = pd.DataFrame(Stop.objects.values(*cols),
                                columns=cols)
        assert df['from_stop'].isin(df_stops['id']).all(), 'Von-Haltestelle nicht in Haltestellennummern'
        assert df['to_stop'].isin(df_stops['id']).all(), 'Nach-Haltestelle nicht in Haltestellennummern'

        df.rename(columns={'from_stop': 'from_stop_id',
                           'to_stop': 'to_stop_id',}, inplace=True)

        variant = request.data.get('variant')
        df['variant_id'] = int(variant)
        return df


class MatrixCellPlaceSerializer(serializers.Serializer):
    drop_constraints = BooleanField(default=True)

    class Meta:
        model = MatrixCellPlace
        fields = ('cell_id', 'place_id', 'minutes')

    def calculate_traveltimes(self, request) -> pd.DataFrame:
        """calculate traveltimes"""
        cell_tbl = RasterCell._meta.db_table
        rcp_tbl = RasterCellPopulation._meta.db_table
        place_tbl = Place._meta.db_table

        max_distance = float(request.data.get('max_distance'))
        speed = float(request.data.get('speed'))
        variant = int(request.data.get('variant'))

        params = (speed, max_distance)

        query = f'''SELECT
        c.id AS cell_id,
        p.id AS place_id,
        st_distance(c."pnt", p."geom") / %s * (6.0/1000) AS minutes
        FROM "{cell_tbl}" AS c,
        (SELECT DISTINCT cell_id
        FROM "{rcp_tbl}") AS r,
        "{place_tbl}" AS p
        WHERE c.id = r.cell_id
        AND st_dwithin(c."pnt", p."geom", %s)
        '''
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            df = pd.DataFrame(cursor.fetchall(),
                              columns=self.Meta.fields)

        df['variant_id'] = variant

        return df