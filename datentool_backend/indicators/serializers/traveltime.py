import os
import pandas as pd
from tempfile import mktemp

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation

from django.conf import settings
from django.db import connection

from rest_framework import serializers
from rest_framework.fields import FileField, IntegerField, BooleanField

from matrixconverters.read_ptv import ReadPTVMatrix

from datentool_backend.modes.models import (MODE_MAX_DISTANCE, MODE_SPEED,
                                            ModeVariant)
from datentool_backend.indicators.models import (Stop,
                                                 MatrixStopStop,
                                                 MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )
from datentool_backend.infrastructure.models.places import Place
from datentool_backend.population.models import RasterCell, RasterCellPopulation


class MatrixStopStopTemplateSerializer(serializers.Serializer):
    """Serializer for uploading MatrixStopStopTemplate"""
    excel_or_visum_file = FileField()
    variant = IntegerField()
    drop_constraints = BooleanField(default=True)

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

    def read_excel_file(self, request) -> pd.DataFrame:
        """read excelfile and return a dataframe"""
        excel_or_visum_file = request.FILES['excel_or_visum_file']

        try:
            df = pd.read_excel(excel_or_visum_file.file,
                               sheet_name='Reisezeit',
                               skiprows=[1])

        except ValueError as e:
            # read PTV-Matrix
            fn = mktemp(suffix='.mtx')
            with open(fn, 'wb') as tfile:
                tfile.write(excel_or_visum_file.file.read())
            da = ReadPTVMatrix(fn)
            os.remove(fn)

            df = da['matrix'].to_dataframe()
            df = df.loc[df['matrix']<999999]
            df.index.rename(['from_stop', 'to_stop'], inplace=True)
            df.rename(columns={'matrix': 'minutes',}, inplace=True)
            df.reset_index(inplace=True)

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


class MatrixAirDistanceMixin(serializers.Serializer):
    drop_constraints = BooleanField(default=True)

    def get_queryset(self, request):
        variant = ModeVariant.objects.get(id=request.data.get('variant'))
        return MatrixCellPlace.objects.filter(variant_id=variant)

    def calculate_traveltimes(self, request) -> pd.DataFrame:
        """calculate traveltimes"""

        variant = ModeVariant.objects.get(id=request.data.get('variant'))
        max_distance = MODE_MAX_DISTANCE[variant.mode]
        speed = MODE_SPEED[variant.mode]

        query = self.get_query()
        params = (speed, max_distance)

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            df = pd.DataFrame(cursor.fetchall(),
                              columns=self.Meta.fields)

        df['variant_id'] = variant.id

        return df


class MatrixCellStopSerializer(MatrixAirDistanceMixin):

    class Meta:
        model = MatrixCellStop
        fields = ('cell_id', 'stop_id', 'minutes')

    def get_query(self) -> str:

        cell_tbl = RasterCell._meta.db_table
        rcp_tbl = RasterCellPopulation._meta.db_table
        stop_tbl = Stop._meta.db_table

        query = f'''SELECT
        c.id AS cell_id,
        s.id AS stop_id,
        st_distance(c."pnt_25832", s."pnt_25832") / %s * (6.0/1000) AS minutes
        FROM
        (SELECT
        c.id,
        c.pnt,
        st_transform(c.pnt, 25832) AS pnt_25832
        FROM "{cell_tbl}" AS c) AS c,
        (SELECT DISTINCT cell_id
        FROM "{rcp_tbl}") AS r,
        (SELECT s.id,
        s.geom,
        st_transform(s.geom, 25832) AS pnt_25832,
        cosd(st_y(st_transform(s.geom, 4326))) AS kf
        FROM "{stop_tbl}" AS s) AS s
        WHERE c.id = r.cell_id
        AND st_dwithin(c."pnt", s."geom", %s * s.kf)
        '''
        return query


class MatrixCellPlaceSerializer(MatrixAirDistanceMixin):

    class Meta:
        model = MatrixCellPlace
        fields = ('cell_id', 'place_id', 'minutes')

    def get_query(self) -> str:

        cell_tbl = RasterCell._meta.db_table
        rcp_tbl = RasterCellPopulation._meta.db_table
        place_tbl = Place._meta.db_table

        query = f'''SELECT
        c.id AS cell_id,
        p.id AS place_id,
        st_distance(c."pnt_25832", p."pnt_25832") / %s * (6.0/1000) AS minutes
        FROM
        (SELECT
        c.id,
        c.pnt,
        st_transform(c.pnt, 25832) AS pnt_25832
        FROM "{cell_tbl}" AS c) AS c,
        (SELECT DISTINCT cell_id
        FROM "{rcp_tbl}") AS r,
        (SELECT p.id,
        p.geom,
        st_transform(p.geom, 25832) AS pnt_25832,
        cosd(st_y(st_transform(p.geom, 4326))) AS kf
        FROM "{place_tbl}" AS p) AS p
        WHERE c.id = r.cell_id
        AND st_dwithin(c."pnt", p."geom", %s * p.kf)
        '''
        return query


class MatrixPlaceStopSerializer(MatrixAirDistanceMixin):

    class Meta:
        model = MatrixPlaceStop
        fields = ('place_id', 'stop_id', 'minutes')

    def get_query(self) -> str:

        place_tbl = Place._meta.db_table
        stop_tbl = Stop._meta.db_table

        query = f'''SELECT
        p.id AS place_id,
        s.id AS stop_id,
        st_distance(p."pnt_25832", p."pnt_25832") / %s * (6.0/1000) AS minutes
        FROM
        (SELECT
        s.id,
        s.geom,
        st_transform(s.geom, 25832) AS pnt_25832
        FROM "{stop_tbl}" AS s) AS s,
        (SELECT p.id,
        p.geom,
        st_transform(p.geom, 25832) AS pnt_25832,
        cosd(st_y(st_transform(p.geom, 4326))) AS kf
        FROM "{place_tbl}" AS p) AS p
        WHERE st_dwithin(s."geom", p."geom", %s * p.kf)
        '''
        return query
