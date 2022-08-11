import logging
logger = logging.getLogger(__name__)

import pandas as pd
from typing import List, Tuple
from io import StringIO
from distutils.util import strtobool
from urllib.parse import urlencode

from django.db import transaction, connection
from django.http.request import QueryDict, MultiValueDict, HttpRequest
from django.db.models.query import QuerySet
from django.conf import settings
from django.db.models import FloatField
from django.contrib.gis.db.models.functions import Transform, Func

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse

from routingpy import OSRM


from datentool_backend.utils.excel_template import ExcelTemplateMixin
from datentool_backend.utils.serializers import MessageSerializer, drop_constraints
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.population.models import RasterCell, RasterCellPopulation

from datentool_backend.indicators.models import (Stop,
                                                 MatrixStopStop,
                                                 Router,
                                                 Place,
                                                 MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )

from datentool_backend.modes.models import (ModeVariant,
                                            Mode,
                                            MODE_MAX_DISTANCE,
                                            DEFAULT_MAX_DIRECT_WALKTIME,
                                            MODE_SPEED,
                                            )

from datentool_backend.indicators.serializers import (StopSerializer,
                                                      StopTemplateSerializer,
                                                      MatrixStopStopTemplateSerializer,
                                                      RouterSerializer,
                                                      )
from datentool_backend.utils.processes import ProtectedProcessManager


class RoutingError(Exception):
    """A Routing Error"""


air_distance_routing = serializers.BooleanField(
    default=False,
    label='use air distance for routing',
    help_text='Set to True for air-distance routing')


class StopViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    serializer_action_classes = {'upload_template': StopTemplateSerializer,
                                 'create_template': StopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = int(self.request.data.get('variant'))
        return Stop.objects.filter(variant=variant)


class MatrixStopStopViewSet(ExcelTemplateMixin,
                            viewsets.GenericViewSet):
    serializer_class = MatrixStopStopTemplateSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixStopStop.objects.filter(variant=variant)


    @extend_schema(description='Upload Excel-File or PTV-Visum-Matrix with Traveltimes from Stop to Stop',
                   request=inline_serializer(
                       name='FileDropConstraintModeVariantSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'variant': serializers.PrimaryKeyRelatedField(
                           queryset=ModeVariant.objects.all(),
                           help_text='mode_variant_id',),
                               'excel_or_visum_file': serializers.FileField(help_text='Excel- or PTV-Visum-Matrix'),
                               },
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        with ProtectedProcessManager(request.user):
            return super().upload_template(request)


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class TravelTimeRouterMixin(viewsets.GenericViewSet):
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    columns: List[str] = []

    @extend_schema(description='Create Traveltime Matrix',
                   request=inline_serializer(
                       name='TravelTimeSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'air_distance_routing': air_distance_routing,
                               'variants': serializers.ListField(
                                   child=serializers.PrimaryKeyRelatedField(
                                       queryset=ModeVariant.objects.all()
                                   ),
                                   help_text='mode_variant_ids',),
                               'places': serializers.ListField(
                                   child=serializers.PrimaryKeyRelatedField(
                                       queryset=Place.objects.all()
                                   ),
                                   help_text='place_ids',),
                           'access_variant': serializers.PrimaryKeyRelatedField(
                                   queryset=ModeVariant.objects.exclude(mode=Mode.TRANSIT),
                                   help_text='access_mode_variant_id',),
                           'max_distance': serializers.FloatField(),
                           'max_access_distance': serializers.FloatField(),
                           'max_direct_walktime': serializers.FloatField(),

                               }
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Calculation successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Calculation failed')})
    @action(methods=['POST'], detail=False)
    def precalculate_traveltime(self, request):
        """Calculate traveltime with a air distance or network router"""
        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))
        variants = request.data.getlist('variants')
        air_distance_routing = bool(strtobool(
            request.data.get('air_distance_routing', 'False')))
        places = request.data.getlist('places')

        dataframes = []
        try:
            for variant_id in variants:

                queryset = self.get_filtered_queryset(variant_id=variant_id, places=places)
                variant = ModeVariant.objects.get(pk=variant_id)
                max_distance = float(request.data.get('max_distance',
                                                MODE_MAX_DISTANCE[variant.mode]))

                if variant.mode == Mode.TRANSIT:
                    #  access variant is WALK, if no other mode is requested
                    access_variant = ModeVariant.objects.get(
                        id=request.data.get('access_variant',
                                            Mode.WALK))
                    max_access_distance = float(
                        request.data.get('max_access_distance',
                                         MODE_MAX_DISTANCE[variant.mode]))
                    max_direct_walktime = float(
                        request.data.get('max_direct_walktime',
                                         DEFAULT_MAX_DIRECT_WALKTIME))
                    df = self.prepare_and_calc_transit_traveltimes(
                        access_variant,
                        places,
                        max_access_distance,
                        drop_constraints,
                        variant,
                        max_direct_walktime,
                    )
                else:

                    if air_distance_routing:
                        df = self.calculate_airdistance_traveltimes(
                            variant,
                            places=places,
                            max_distance=max_distance,
                            )
                    else:
                        df = self.calc_routed_traveltimes(variant,
                                                          places=places,
                                                          max_distance=max_distance,
                                                          )
                dataframes.append(df)
            if not dataframes:
                msg = 'No routes found'
                raise RoutingError(msg)
            else:
                df = pd.concat(dataframes)
                success, msg = self.save_df(df, queryset, drop_constraints)
                if not success:
                    raise RoutingError(msg)

        except RoutingError as err:
            ret_status = status.HTTP_406_NOT_ACCEPTABLE
            msg = str(err)
        else:
            ret_status = status.HTTP_202_ACCEPTED
        logger.info(msg)
        return Response({'message': msg, }, status=ret_status)

    def prepare_and_calc_transit_traveltimes(self,
                                             access_variant: ModeVariant,
                                             places: List[int],
                                             max_distance: float,
                                             drop_constraints: bool,
                                             variant: ModeVariant,
                                             max_direct_walktime: float,
                                             ) -> pd.DataFrame:
        # calculate time from place to stop
        matrix_place_stop = MatrixPlaceStopViewSet()
        df_ps = matrix_place_stop.calc_routed_traveltimes(
            variant=access_variant,
            places=places,
            max_distance=max_distance,
        )
        qs = matrix_place_stop.get_filtered_queryset(
            variant_id=access_variant.pk,
            places=places)
        success, msg = matrix_place_stop.save_df(df_ps, qs, drop_constraints)
        if not success:
            raise RoutingError(msg)

        # calculate time from cell to stop
        matrix_cell_stop = MatrixCellStopViewSet()
        df_cs = matrix_cell_stop.calc_routed_traveltimes(
            variant=access_variant,
            max_distance=max_distance,
        )
        qs = matrix_cell_stop.get_filtered_queryset(
            variant_id=access_variant.pk)
        success, msg = matrix_cell_stop.save_df(df_cs, qs, drop_constraints)
        if not success:
            raise RoutingError(msg)

        logger.info(msg)
        df = self.calculate_transit_traveltime(
            access_variant=access_variant,
            transit_variant=variant,
            places=places,
            max_direct_walktime=max_direct_walktime,
        )
        return df

    def save_df(self,
                df: pd.DataFrame,
                queryset: QuerySet,
                drop_constraints: bool) -> (bool, str):
        model = queryset.model
        manager = model.copymanager
        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

            n_deleted, deleted_rows = queryset.delete()

            try:

                with StringIO() as file:
                    df.to_csv(file, index=False)
                    file.seek(0)
                    model.copymanager.from_csv(
                        file,
                        drop_constraints=False, drop_indexes=False,
                    )

            except Exception as e:
                msg = str(e)
                return (False, msg)

            finally:
                # recreate indices
                if drop_constraints:
                    manager.restore_constraints()
                    manager.restore_indexes()
            msg = f'Traveltime Calculation successful, deleted {n_deleted} rows and added {len(df)} rows to {model._meta.object_name}'
            return (True, msg)

    def get_filtered_queryset(variant_id: int, **kwargs) -> QuerySet:
        raise NotImplementedError()

    def get_sources(self, **kwargs) -> QuerySet:
        raise NotImplementedError()

    def get_destinations(self, **kwargs) -> QuerySet:
        raise NotImplementedError('Has to be implemented in the subclass')

    def calc_routed_traveltimes(self,
                                variant: ModeVariant,
                                max_distance: float,
                                **kwargs) -> pd.DataFrame:
        """calculate traveltimes"""
        port = settings.MODE_OSRM_PORTS[Mode(variant.mode).name]

        sources = self.get_sources(**kwargs)
        destinations = self.get_destinations(**kwargs)

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
        meters.index.names = self.columns

        seconds = arr_seconds.T.unstack()
        seconds.index.names = self.columns
        seconds = seconds.loc[meters<max_distance]
        minutes = seconds / 60
        df = minutes.to_frame(name='minutes')
        df['variant_id'] = variant.id
        df.reset_index(inplace=True)
        return df

    def calculate_airdistance_traveltimes(self,
                                          variant: ModeVariant,
                                          max_distance: float,
                                          **kwargs) -> pd.DataFrame:
        """calculate traveltimes"""

        speed = MODE_SPEED[variant.mode]

        query, params = self.get_airdistance_query(speed=speed,
                                                   max_distance=max_distance,
                                                   **kwargs)

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = self.columns + ['minutes']
            df = pd.DataFrame(cursor.fetchall(),
                              columns=columns)

        df['variant_id'] = variant.id

        return df

    def calculate_transit_traveltime(self,
                                     access_variant: ModeVariant,
                                     transit_variant: ModeVariant,
                                     max_direct_walktime: float,
                                     **kwargs) -> pd.DataFrame:
        raise NotImplementedError()

    def get_airdistance_query(self,
                              variant: ModeVariant,
                              speed: float,
                              max_distance: float,
                              **kwargs) -> str:
        raise NotImplementedError()


class MatrixCellPlaceViewSet(TravelTimeRouterMixin):
    columns = ['place_id', 'cell_id']

    def get_filtered_queryset(self,
                              variant_id: int,
                              places: List[int] = None,
                              **kwargs) -> QuerySet:
        qs = MatrixCellPlace.objects.filter(variant_id=variant_id)
        if places:
            qs = qs.filter(place_id__in=places)
        return qs

    def get_sources(self, places, **kwargs):
        sources = Place.objects.all()
        if places:
            sources = sources.filter(id__in=places)
        sources = sources\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs', function='ST_Y', output_field=FloatField()),
                  lon=Func('wgs', function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return sources

    def get_destinations(self, **kwargs):
        destinations = RasterCell.objects.filter(rastercellpopulation__isnull=False)\
            .annotate(wgs=Transform('pnt', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return destinations

    def calculate_transit_traveltime(self,
                                     access_variant: ModeVariant,
                                     transit_variant: ModeVariant,
                                     max_direct_walktime: float,
                                     **kwargs) -> pd.DataFrame:

        # travel time place to stop
        q_placestop, p_placestop = MatrixPlaceStop.objects.filter(
            variant=access_variant).query.sql_with_params()
        # travel time cell to stop
        q_cellstop, p_cellstop = MatrixCellStop.objects.filter(
            variant=access_variant).query.sql_with_params()
        # travel time between stops
        q_stopstop, p_stopstop = MatrixStopStop.objects.filter(
            variant=transit_variant).query.sql_with_params()
        # direct traveltime by foot (or other access mode), if it is shorter than max_direct_walktime
        q_cellplace, p_cellplace = MatrixCellPlace.objects.filter(
            variant=access_variant,
            minutes__lt=max_direct_walktime,
        ).query.sql_with_params()

        query = f'''
        SELECT
          COALESCE(t.place_id, a.place_id) AS place_id,
          COALESCE(t.cell_id, a.cell_id) AS cell_id,
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
            columns = self.columns + ['minutes']
            df = pd.DataFrame(cursor.fetchall(),
                              columns=columns)

        df['variant_id'] = transit_variant.id

        return df

    def get_airdistance_query(self,
                              speed: float,
                              max_distance: float,
                              places: List[int] = [],
                              **kwargs) -> str:
        """
        returns a query and its parameters to calculate the air distance
        Parameters
        ----------
        speed: float
        max_distance: float
        places: List[int], optional

        Returns
        -------
        query: sql
        params: tuple
        """

        cell_tbl = RasterCell._meta.db_table
        rcp_tbl = RasterCellPopulation._meta.db_table
        place_tbl = Place._meta.db_table

        places = self.get_sources(places=places)
        p_places = list(places.values_list('id', flat=True))

        query = f'''SELECT
        p.id AS place_id,
        c.id AS cell_id,
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
        FROM "{place_tbl}" AS p
        WHERE p.id = ANY(%s)) AS p
        WHERE c.id = r.cell_id
        AND st_dwithin(c."pnt", p."geom", %s * p.kf)
        '''

        params = (speed, p_places, max_distance)

        return query, params

class MatrixCellStopViewSet(TravelTimeRouterMixin):
    columns = ['cell_id', 'stop_id']

    def get_filtered_queryset(self, variant_id: int, **kwargs) -> QuerySet:
        return MatrixCellStop.objects.filter(variant_id=variant_id)

    def get_sources(self, **kwargs):
        sources =  RasterCell.objects.filter(rastercellpopulation__isnull=False)\
            .annotate(wgs=Transform('pnt', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return sources
    def get_destinations(self, **kwargs):
        destinations = Stop.objects.all()\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs', function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs', function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return destinations

    def get_airdistance_query(self,
                              speed: float,
                              max_distance: float,
                              **kwargs) -> str:
        """
        returns a query and its parameters to calculate the air distance
        Parameters
        ----------
        speed: float
        max_distance: float

        Returns
        -------
        query: sql
        params: tuple
        """

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
        params = (speed, max_distance)
        return query, params


class MatrixPlaceStopViewSet(TravelTimeRouterMixin):
    columns = ['place_id', 'stop_id']

    def get_filtered_queryset(self,
                              variant_id: int,
                              places: List[int] = None,
                              **kwargs) -> QuerySet:
        qs = MatrixPlaceStop.objects.filter(variant_id=variant_id)
        if places:
            qs = qs.filter(place_id__in=places)
        return qs

    def get_sources(self, places, **kwargs) -> Place:
        sources = Place.objects.all()
        if places:
            sources = sources.filter(id__in=places)
        sources = sources\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return sources

    def get_destinations(self, **kwargs) -> Stop:
        destinations = Stop.objects.all()\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs', function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs', function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return destinations

    def get_airdistance_query(self,
                              speed: float,
                              max_distance: float,
                              places: List[int] = [],
                              **kwargs,
                              ) -> Tuple[str, tuple]:
        """
        returns a query and its parameters to calculate the air distance
        Parameters
        ----------
        speed: float
        max_distance: float
        places: List[int], optional

        Returns
        -------
        query: sql
        params: tuple
        """

        place_tbl = Place._meta.db_table
        stop_tbl = Stop._meta.db_table

        places = self.get_sources(places=places)
        p_places = list(places.values_list('id', flat=True))

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
        FROM "{place_tbl}" AS p
        WHERE p.id = ANY(%s)) AS p
        WHERE st_dwithin(s."geom", p."geom", %s * p.kf)
        '''
        params = (speed, p_places, max_distance)
        return query, params
