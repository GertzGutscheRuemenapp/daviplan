import os
import pandas as pd
from tempfile import mktemp

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation

from django.conf import settings
from django.db import connection
from django.db.models import FloatField
from django.contrib.gis.db.models.functions import Transform, Func

from rest_framework import serializers
from rest_framework.fields import FileField, IntegerField, BooleanField

from matrixconverters.read_ptv import ReadPTVMatrix

from routingpy import OSRM

from datentool_backend.modes.models import (MODE_MAX_DISTANCE,
                                            MODE_SPEED,
                                            MODE_OSRM_PORTS,
                                            ModeVariant,
                                            Mode)
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


class MatrixRoutedDistanceMixin(serializers.Serializer):
    drop_constraints = BooleanField(default=True)

    def calculate_transit_traveltime(self) -> pd.DataFrame:
        raise NotImplementedError()

    def calculate_traveltimes(self, request) -> pd.DataFrame:
        """calculate traveltimes"""

        variant = ModeVariant.objects.get(id=request.data.get('variant'))
        if variant.mode == Mode.TRANSIT:
            access_variant = ModeVariant.objects.get(
                id=request.data.get('access_variant'))
            return self.calculate_transit_traveltime(
                access_variant=access_variant,
                transit_variant=variant,
            )

        port = MODE_OSRM_PORTS[variant.mode]
        max_distance = int(request.data.get('max_distance',
                                            MODE_MAX_DISTANCE[variant.mode]))

        sources = self.get_sources()
        destinations = self.get_destinations()

        client = OSRM(base_url=f'http://{settings.ROUTING_HOST}:{port}')
        # as lists
        coords = list(sources.values_list('lon', 'lat', named=False))\
            + list(destinations.values_list('lon', 'lat', named=False))
        #radiuses = [30000 for i in range(len(coords))]
        matrix = client.matrix(locations=coords,
                               #radiuses=radiuses,
                               sources=range(len(sources)),
                               destinations=range(len(sources), len(coords)),
                               profile='driving')
        # convert matrix to dataframe
        arr_seconds = pd.DataFrame(
            matrix.durations,
            index=list(sources.values_list('id', flat=True)),
            columns=list(destinations.values_list('id', flat=True)))
        arr_meters = pd.DataFrame(
            matrix.distances,
            index=list(sources.values_list('id', flat=True)),
            columns=list(destinations.values_list('id', flat=True)))

        meters = arr_meters.T.unstack()
        meters.index.names = self.col_ids

        seconds = arr_seconds.T.unstack()
        seconds.index.names = self.col_ids
        seconds = seconds.loc[meters<max_distance]
        minutes = seconds / 60
        df = minutes.to_frame(name='minutes')
        df['variant_id'] = variant.id
        df.reset_index(inplace=True)
        return df


class MatrixCellStopSerializerMixin:

    class Meta:
        model = MatrixCellStop
        fields = ('cell_id', 'stop_id', 'minutes')

    def get_queryset(self, request):
        variant = ModeVariant.objects.get(id=request.data.get('variant'))
        return MatrixCellStop.objects.filter(variant_id=variant)


class MatrixCellStopSerializer(MatrixCellStopSerializerMixin,
                               MatrixAirDistanceMixin):

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


class MatrixRoutedCellStopSerializer(MatrixCellStopSerializerMixin,
                                      MatrixRoutedDistanceMixin):
    """Routed traveltimes from Cell to Stop"""
    col_ids = ('cell_id', 'stop_id')

    def get_destinations(self):
        destinations = Stop.objects.all()\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs', function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs', function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return destinations

    def get_sources(self):
        sources =  RasterCell.objects.filter(rastercellpopulation__isnull=False)\
            .annotate(wgs=Transform('pnt', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return sources


class MatrixCellPlaceSerializerMixin:

    class Meta:
        model = MatrixCellPlace
        fields = ('cell_id', 'place_id', 'minutes')

    def get_queryset(self, request):
        variant = ModeVariant.objects.get(id=request.data.get('variant'))
        return MatrixCellPlace.objects.filter(variant_id=variant)

class MatrixCellPlaceSerializer(MatrixCellPlaceSerializerMixin,
                                MatrixAirDistanceMixin):

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


class MatrixRoutedCellPlaceSerializer(MatrixCellPlaceSerializerMixin,
                                      MatrixRoutedDistanceMixin):
    """Routed traveltimes from cell to place"""
    col_ids = ('place_id', 'cell_id')

    def get_destinations(self):
        destinations = RasterCell.objects.filter(rastercellpopulation__isnull=False)\
            .annotate(wgs=Transform('pnt', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return destinations

    def get_sources(self):
        sources = Place.objects.all()\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return sources

    def calculate_transit_traveltime(self,
                                     access_variant: ModeVariant,
                                     transit_variant: ModeVariant) -> pd.DataFrame:

        q_placestop, p_placestop = MatrixPlaceStop.objects.filter(
            variant=access_variant).query.sql_with_params()
        q_cellstop, p_cellstop = MatrixCellStop.objects.filter(
            variant=access_variant).query.sql_with_params()
        q_stopstop, p_stopstop = MatrixStopStop.objects.filter(
            variant=transit_variant).query.sql_with_params()
        q_cellplace, p_cellplace = MatrixCellPlace.objects.filter(
            variant=access_variant).query.sql_with_params()

        query = f'''
        SELECT
          COALESCE(t.cell_id, a.cell_id) AS cell_id,
          COALESCE(t.place_id, a.place_id) AS place_id,
          least(t.minutes, a.minutes) AS minutes
        FROM
        (SELECT
          cs.cell_id,
          sp.place_id,
          min(sp.minutes + cs.minutes) AS minutes
        FROM
        (SELECT
          ss.from_stop_id,
          ps.place_id,
          min(ps.minutes + ss.minutes) AS minutes
        FROM
          ({q_placestop}) ps,
          ({q_stopstop}) ss
        WHERE ps.stop_id = ss.to_stop_id
        GROUP BY
          ss.from_stop_id,
          ps.place_id
        ) sp,
        ({q_cellstop}) cs
        WHERE cs.stop_id = sp.from_stop_id
        GROUP BY
          cs.cell_id,
          sp.place_id) AS t
        FULL OUTER JOIN ({q_cellplace}) a
        ON (t.cell_id = a.cell_id
        AND t.place_id = a.place_id)
        '''
        params = p_placestop + p_stopstop + p_cellstop + p_cellplace


        with connection.cursor() as cursor:
            cursor.execute(query, params)
            df = pd.DataFrame(cursor.fetchall(),
                              columns=self.Meta.fields)

        df['variant_id'] = transit_variant.id

        return df

class MatrixPlaceStopSerializerMixin:

    class Meta:
        model = MatrixPlaceStop
        fields = ('place_id', 'stop_id', 'minutes')

    def get_queryset(self, request):
        variant = ModeVariant.objects.get(id=request.data.get('variant'))
        return MatrixPlaceStop.objects.filter(variant_id=variant)


class MatrixPlaceStopSerializer(MatrixPlaceStopSerializerMixin, MatrixAirDistanceMixin):

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


class MatrixRoutedPlaceStopSerializer(MatrixPlaceStopSerializerMixin,
                                      MatrixRoutedDistanceMixin):
    """Routed traveltimes from place to Stop"""
    col_ids = ('place_id', 'stop_id')

    def get_destinations(self):
        destinations = Stop.objects.all()\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs', function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs', function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return destinations

    def get_sources(self):
        sources = Place.objects.all()\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return sources

