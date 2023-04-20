import logging
import locale

import pandas as pd
import numpy as np
from typing import List, Tuple
from io import StringIO

from django.conf import settings
from django.db import transaction, connection
from django.db.models.query import QuerySet
from django.db.models import FloatField, Q, Model
from django.contrib.gis.db.models.functions import Transform, Func
from requests.exceptions import ConnectionError

from datentool_backend.utils.routers import OSRMRouter
from datentool_backend.utils.raw_delete import delete_chunks

from datentool_backend.population.models import RasterCell, RasterCellPopulation

from datentool_backend.indicators.models import (Stop,
                                                 MatrixStopStop,
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
                                            get_default_access_variant,
                                            )

class RoutingError(Exception):
    """A Routing Error"""


class TravelTimeRouterMixin:
    columns: List[str] = []
    partition_columns: List[str] = []

    def calc(self,
             variant_ids: List[int],
             place_ids: List[int],
             drop_constraints: bool,
             logger: logging.Logger,
             max_distance: float = None,
             access_variant_id: int = None,
             max_access_distance: float = None,
             max_direct_walktime: float = None,
             air_distance_routing: bool = False,
             ):
        variant_ids = variant_ids or ModeVariant.objects.values_list('id', flat=True)
        variants = ModeVariant.objects.filter(id__in=variant_ids).order_by('mode')
        routes_found = 0
        try:
            for variant in variants:
                logger.info('Berechne Reisezeiten für Modus '
                            f'{Mode(variant.mode).name}')
                max_distance_mode = float(max_distance or
                                          MODE_MAX_DISTANCE[variant.mode])
                if variant.mode == Mode.TRANSIT:
                    #  access variant is WALK, if no other mode is requested
                    if access_variant_id:
                        access_variant = ModeVariant.objects.get(id=access_variant_id)
                    else:
                        access_variant = ModeVariant.objects.get(id=get_default_access_variant())
                    av_id = access_variant.id

                    max_access_distance = float(max_access_distance or
                                                MODE_MAX_DISTANCE[variant.mode])
                    max_direct_walktime = float(max_direct_walktime or
                                                DEFAULT_MAX_DIRECT_WALKTIME)

                    n_calculated = self.prepare_and_calc_transit_traveltimes(
                        logger,
                        access_variant,
                        place_ids,
                        max_access_distance,
                        drop_constraints,
                        variant,
                        max_direct_walktime,
                    )
                    routes_found += n_calculated

                else:
                    av_id = None
                    if air_distance_routing:
                        df = self.calculate_airdistance_traveltimes(
                            access_variant=variant,
                            max_distance=max_distance_mode,
                            place_ids=place_ids,
                            logger=logger,
                        )
                        routes_found += len(df)
                        self.store_to_database(df, variant, av_id,
                                               place_ids,
                                               logger, drop_constraints)
                    else:
                        if not place_ids:
                            place_ids = Place.objects.values_list('id', flat=True)
                        chunk_size = 100
                        for i in range(0, len(place_ids), chunk_size):
                            place_part_ids = place_ids[i:i+chunk_size]

                            df = self.calc_routed_traveltimes(
                                variant,
                                max_distance=max_distance_mode,
                                logger=logger,
                                place_ids=place_part_ids)
                            routes_found += len(df)
                            logger.info(f'{min((i+chunk_size), len(place_ids)):n}/'
                                        f'{len(place_ids):n} Orten berechnet')
                            self.store_to_database(df, variant, av_id,
                                                   place_part_ids,
                                                   logger, drop_constraints)

            if not routes_found:
                msg = 'Keine Routen gefunden'
                raise RoutingError(msg)

        except RoutingError as err:
            msg = str(err)
            logger.error(msg)
            raise Exception(msg)
        else:
            logger.info('Berechnung der Reisezeitmatrizen erfolgreich abgeschlossen')

    def store_to_database(self,
                          df: pd.DataFrame,
                          variant: ModeVariant,
                          av_id: int,
                          place_ids: List[int],
                          logger: logging.Logger,
                          drop_constraints: bool):
        """Store Dataframe to Database"""
        if 'access_variant_id' in df.columns:
            df = df.astype(dtype={'access_variant_id': 'Int64' ,})
        queryset = self.get_filtered_queryset(variant_ids=[variant.pk],
                                              access_variant_id=av_id,
                                              place_ids=place_ids)
        df, ignore_columns = self.add_partition_key(
            df,
            variant_id=variant.pk,
            place_ids=df.place_id)
        self.write_results_to_database(logger,
                                       queryset,
                                       df,
                                       drop_constraints,
                                       ignore_columns=ignore_columns)

    def write_results_to_database(self,
                                  logger: logging.Logger,
                                  queryset: QuerySet,
                                  df: pd.DataFrame,
                                  drop_constraints: bool,
                                  stepsize: int = settings.STEPSIZE,
                                  ignore_columns: List[str]=[]):
        """
        Write results of Dataframe to database in chunks
        """
        logger.debug('Schreibe Ergebnisse in die Datenbank')

        delete_chunks(queryset, logger)
        model = queryset.model
        model_name = model._meta.object_name

        n_rows = len(df)
        logger.debug(f'Schreibe insgesamt {n_rows:n} {model_name}-Einträge')
        for i in np.arange(0, n_rows, stepsize, dtype=np.int64):
            chunk = df.iloc[i:i + stepsize]
            model.add_n_rels(chunk)
            # ignore columns that should not be saved to database
            for ignore_column in ignore_columns:
                del(chunk[ignore_column])
            self.save_df(chunk,
                         model,
                         drop_constraints=drop_constraints)
            n_inserted = len(chunk)
            logger.debug(f'{i + n_inserted:n}/{n_rows:n} {model_name}'
                         '-Einträgen geschrieben')
        msg = (f'{n_rows:n} {model_name}-Einträge geschrieben')
        logger.debug(msg)

    def prepare_and_calc_transit_traveltimes(self,
                                             logger: logging.Logger,
                                             access_variant: ModeVariant,
                                             place_ids: List[int],
                                             max_distance: float,
                                             drop_constraints: bool,
                                             variant: ModeVariant,
                                             max_direct_walktime: float,
                                             ) -> int:
        # calculate time from place to stop
        matrix_place_stop = MatrixPlaceStopRouter()
        df_ps = matrix_place_stop.calc_routed_traveltimes(
            variant=access_variant,
            transit_variant=variant,
            place_ids=place_ids,
            max_distance=max_distance,
            logger=logger,
        )
        df_ps.rename(columns={'variant_id': 'access_variant_id', }, inplace=True)

        df_ps, ignore_columns = matrix_place_stop.add_partition_key(
            df_ps,
            transit_variant_id=variant.pk,
            place_ids=df_ps.place_id)
        qs = matrix_place_stop.get_filtered_queryset(
            variant_ids=[variant.pk],
            access_variant_id=access_variant.pk,
            place_ids=place_ids)
        self.write_results_to_database(logger, qs, df_ps, drop_constraints,
                                       ignore_columns=ignore_columns,
                                       )

        # calculate time from stop to cell
        matrix_cell_stop = MatrixCellStopRouter()
        logger.info(f'Berechne Wegezeiten zwischen Siedlungszellen und den '
                    f'Haltestellen mit Modus {Mode(access_variant.mode).name}')
        stops = Stop.objects.filter(variant=variant).values_list('id', flat=True)
        n_stops = len(stops)
        chunk_size = 100

        for i in range(0, n_stops, chunk_size):
            stops_part = stops[i:i + chunk_size]
            df_cs = matrix_cell_stop.calc_routed_traveltimes(
                variant=access_variant,
                transit_variant=variant,
                max_distance=max_distance,
                stops=stops_part,
                logger=logger,
            )
            df_cs.rename(columns={'variant_id': 'access_variant_id', },
                         inplace=True)

            logger.info(f'{min((i+chunk_size), n_stops):n}/'
                        f'{n_stops:n} Haltestellen berechnet')
            self.store_df_cs_to_database(df_cs, variant, access_variant,
                                         stops_part,
                                         logger, drop_constraints)

        logger.info('Berechne Gesamtreisezeiten...')

        if not place_ids:
            place_ids = Place.objects.values_list('id', flat=True)

        n_total = len(place_ids)
        for i in range(0, n_total, chunk_size):
            place_ids_part = place_ids[i:i + chunk_size]
            df = self.calculate_transit_traveltime(
                access_variant=access_variant,
                transit_variant=variant,
                place_ids=place_ids_part,
                max_direct_walktime=max_direct_walktime,
                id_columns=['place_id', 'cell_id'],
            )

            self.store_to_database(df, variant, access_variant.pk,
                                   place_ids_part,
                                   logger, drop_constraints)
            logger.info(f'Gesamtreisezeiten zu '
                        f'{min((i+chunk_size), n_total):n}/'
                        f'{n_total:n} Orten berechnet')

        return n_total

    def store_df_cs_to_database(self,
                                df_cs: pd.DataFrame,
                                variant: ModeVariant,
                                access_variant: ModeVariant,
                                stop_ids: List[int],
                                logger: logging.Logger,
                                drop_constraints: bool):
        """Store DataFrame from Cell to Stop to Database"""
        matrix_cell_stop = MatrixCellStopRouter()
        df_cs, ignore_columns = matrix_cell_stop.add_partition_key(
            df_cs,
            transit_variant_id=variant.pk)

        qs = matrix_cell_stop.get_filtered_queryset(
            variant_ids=[variant.pk],
            access_variant_id=access_variant.pk,
            stop_ids=stop_ids,
        )
        self.write_results_to_database(logger, qs, df_cs, drop_constraints,
                                       ignore_columns=ignore_columns,
                                       )

    @staticmethod
    def annotate_coords(queryset: QuerySet, geom='geom'):
        return queryset.annotate(wgs=Transform(geom, 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')

    @staticmethod
    def route(variant: ModeVariant,
              sources: QuerySet,
              destinations: QuerySet,
              logger: logging.Logger,
              max_distance: float = None,
              id_columns=None,
              ) -> pd.DataFrame:
        """calculate traveltimes"""
        mode = Mode(variant.mode)

        if max_distance is None:
            max_distance = MODE_MAX_DISTANCE[variant.mode]

        router = OSRMRouter(mode)

        if not router.is_running:
            router.run()

        if not (sources.exists() and destinations.exists()):
            id_columns = id_columns or ['source_id', 'destination_id']
            df = pd.DataFrame(columns=id_columns + ['minutes', 'variant_id'])
            return df

        sources = sources.order_by('id')
        destinations = destinations.order_by('id')

        source_coords = list(sources.values_list('lon', 'lat', named=False))
        dest_coords = list(destinations.values_list('lon', 'lat', named=False))

        try:
            matrix = router.matrix_calculation(source_coords, dest_coords)
        # if routing crashes due to malformed network the connection just aborts
        except ConnectionError:
            raise RoutingError('Routing abgebrochen')

        # convert matrix to dataframe
        arr = np.array(matrix.durations)
        arr_seconds = pd.DataFrame(
            arr,
            index=list(sources.values_list('id', flat=True)),
            columns=list(destinations.values_list('id', flat=True)))
        arr = np.array(matrix.distances)
        arr_meters = pd.DataFrame(
            arr,
            index=list(sources.values_list('id', flat=True)),
            columns=list(destinations.values_list('id', flat=True)))

        meters = arr_meters.T.unstack()
        if id_columns:
            meters.index.names = id_columns
        seconds = arr_seconds.T.unstack()
        if id_columns:
            seconds.index.names = id_columns
        seconds = seconds.loc[meters<max_distance]
        minutes = seconds / 60
        df = minutes.to_frame(name='minutes')
        df['variant_id'] = variant.id
        df.reset_index(inplace=True)
        #logger.debug(df)
        return df

    @staticmethod
    def save_df(df: pd.DataFrame,
                model: Model,
                drop_constraints: bool) -> (bool, str):
        manager = model.copymanager
        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

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
                raise RoutingError(msg)

            finally:
                # recreate indices
                if drop_constraints:
                    manager.restore_constraints()
                    manager.restore_indexes()

    def get_filtered_queryset(variant_ids: List[int],
                              access_variant_id:int=None,
                              **kwargs) -> QuerySet:
        raise NotImplementedError()

    def get_sources(self, **kwargs) -> QuerySet:
        raise NotImplementedError()

    def get_destinations(self, **kwargs) -> QuerySet:
        raise NotImplementedError('Has to be implemented in the subclass')

    def calc_routed_traveltimes(self,
                                variant: ModeVariant,
                                max_distance: float,
                                logger: logging.Logger,
                                **kwargs) -> pd.DataFrame:
        """calculate traveltimes"""

        sources = self.get_sources(variant=variant, **kwargs).order_by('id')
        destinations = self.get_destinations(variant=variant, **kwargs).order_by('id')

        # split destinations, if needed
        # OSRM can only handle certain dimensions of inputs
        # seems to be sth like 100 * 50k, the splitting of the source should
        # already have been done outside of this funtion if needed
        chunk_size = 20000
        dataframes = []
        for i in range(0, len(destinations), chunk_size):
            # splitting a queryset by filtering by ids
            dest_part = destinations.filter(
                id__in=destinations.values_list('id')[i:i+chunk_size])
            # key-columns except the last column (partition_id)
            df = self.route(variant,
                            sources,
                            dest_part,
                            logger,
                            max_distance=max_distance,
                            id_columns=self.columns)
            dataframes.append(df)
        return pd.concat(dataframes)

    def calculate_airdistance_traveltimes(self,
                                          access_variant: ModeVariant,
                                          max_distance: float,
                                          logger: logging.Logger,
                                          transit_variant_id: int = None,
                                          **kwargs) -> pd.DataFrame:
        """calculate traveltimes"""
        logger.info('start calculation of air-distance matrix')
        speed = MODE_SPEED[access_variant.mode]

        query, params = self.get_airdistance_query(access_variant_id=access_variant.id,
                                                   speed=speed,
                                                   max_distance=max_distance,
                                                   transit_variant_id=transit_variant_id,
                                                   **kwargs)

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = self.columns + self.partition_columns + ['minutes']
            df = pd.DataFrame(cursor.fetchall(),
                              columns=columns)

        logger.info('calculation of air-distance matrix finished')

        return df

    @staticmethod
    def calculate_transit_traveltime(transit_variant: ModeVariant,
                                     access_variant: ModeVariant,
                                     max_direct_walktime: float,
                                     place_ids: List[int],
                                     id_columns: List[str],
                                     **kwargs) -> pd.DataFrame:
        raise NotImplementedError()

    def get_airdistance_query(self,
                              access_variant: int,
                              speed: float,
                              max_distance: float,
                              transit_variant: int = None,
                              **kwargs) -> str:
        raise NotImplementedError()

    @staticmethod
    def add_partition_key(df: pd.DataFrame, **args) -> Tuple[pd.DataFrame, List[str]]:
        """
        add the partition id to the Dataframe

        Returns
        -------
        the dataframe including the partition_id and a list of column names
        to ignore when uploading the Dataframe to the database
        """
        raise NotImplementedError('To be defined in the subclass')


class MatrixCellPlaceRouter(TravelTimeRouterMixin):
    columns = ['place_id', 'cell_id']
    partition_columns = ['variant_id', 'partition_id']

    def get_filtered_queryset(self,
                              variant_ids: List[int],
                              access_variant_id: int=None,
                              place_ids: List[int] = None,
                              **kwargs) -> QuerySet:
        mode_variants = ModeVariant.objects.filter(id__in=variant_ids)
        private_transport_variants = [variant.pk
                            for variant in mode_variants.exclude(mode=Mode.TRANSIT)]
        transit_variants = [variant.pk
                            for variant in mode_variants.filter(mode=Mode.TRANSIT)]
        qs = MatrixCellPlace.objects.filter(Q(variant__in=private_transport_variants) |
                                            Q(variant__in=transit_variants,
                                              access_variant_id=access_variant_id))
        if place_ids:
            qs = qs.filter(place_id__in=place_ids)
        return qs

    def get_sources(self, place_ids, **kwargs):
        sources = Place.objects.all()
        if place_ids:
            sources = sources.filter(id__in=place_ids)
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

    @staticmethod
    def calculate_transit_traveltime(transit_variant: ModeVariant,
                                     access_variant: ModeVariant,
                                     max_direct_walktime: float,
                                     place_ids: List[int],
                                     id_columns=['place_id', 'cell_id'],
                                     **kwargs) -> pd.DataFrame:
        # travel time place to stop
        qs = MatrixPlaceStop.objects.filter(
            stop__variant=transit_variant,
            access_variant=access_variant,
            )
        if place_ids:
            infrastructure_ids = Place.objects\
                .filter(id__in=place_ids)\
                .order_by('infrastructure_id')\
                .distinct('infrastructure_id')\
                .values_list('infrastructure_id', flat=True)
            partition_ids = [[transit_variant.id, infrastructure_id]
                             for infrastructure_id in infrastructure_ids]
            qs = qs.filter(place_id__in=place_ids,
                           partition_id__in=partition_ids)

        q_placestop, p_placestop = qs.query.sql_with_params()


        # travel time cell to stop
        q_cellstop, p_cellstop = MatrixCellStop.objects.filter(
            transit_variant_id=transit_variant.id,
            access_variant=access_variant).query.sql_with_params()

        # travel time between stops
        q_stopstop, p_stopstop = MatrixStopStop.objects.filter(
            variant_id=transit_variant.id,
            ).query.sql_with_params()

        # direct traveltime by foot (or other access mode), if it is shorter than max_direct_walktime
        qs = MatrixCellPlace.objects.filter(
            variant=access_variant,
            minutes__lt=max_direct_walktime,
        )
        if place_ids:
            qs = qs.filter(place_id__in=place_ids)

        q_cellplace, p_cellplace = qs.query.sql_with_params()

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
            columns = id_columns + ['minutes']
            df = pd.DataFrame(cursor.fetchall(),
                              columns=columns)

        df['variant_id'] = transit_variant.id
        df['access_variant_id'] = access_variant.id

        return df

    def get_airdistance_query(self,
                              access_variant_id: int,
                              speed: float,
                              max_distance: float,
                              place_ids: List[int] = [],
                              **kwargs) -> str:
        """
        returns a query and its parameters to calculate the air distance
        Parameters
        ----------
        speed: float
        max_distance: float
        place_ids: List[int], optional

        Returns
        -------
        query: sql
        params: tuple
        """

        cell_tbl = RasterCell._meta.db_table
        rcp_tbl = RasterCellPopulation._meta.db_table
        place_tbl = Place._meta.db_table

        place_ids = self.get_sources(place_ids=place_ids)
        p_places = list(place_ids.values_list('id', flat=True))

        query = f'''SELECT
        p.id AS place_id,
        c.id AS cell_id,
        %s AS variant_id,
        ARRAY[%s, p.infrastructure_id] AS partition_id,
        st_distance(c."pnt_25832", p."pnt_25832") / %s * (60.0/1000) AS minutes
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
        cosd(st_y(st_transform(p.geom, 4326))) AS kf,
        p.infrastructure_id
        FROM "{place_tbl}" AS p
        WHERE p.id = ANY(%s)) AS p
        WHERE c.id = r.cell_id
        AND st_dwithin(c."pnt", p."geom", %s / p.kf)
        '''

        params = (access_variant_id, access_variant_id, speed, p_places, max_distance)

        return query, params

    @staticmethod
    def add_partition_key(df: pd.DataFrame,
                          variant_id: int,
                          place_ids: List[int]) -> Tuple[pd.DataFrame, List[str]]:
        """add the partition key"""
        df['variant_id'] = variant_id

        # add infrastructure_id
        places_infra = pd.DataFrame(Place.objects.filter(id__in=place_ids)
                                    .values('id', 'infrastructure_id'))\
            .rename(columns={'id': 'place_id'},)\
            .set_index('place_id')

        df = df.merge(places_infra, right_index=True, left_on='place_id')
        def make_partition_key(row):
            return f"{{{row['variant_id']:0.0f},{row['infrastructure_id']:0.0f}}}"
        df['partition_id'] = df.apply(make_partition_key, axis=1)

        ignore_columns = ['infrastructure_id']
        return df, ignore_columns


class AccessTimeRouterMixin(TravelTimeRouterMixin):

    def calc(self,
             variant_ids: List[int],
             place_ids: List[int],
             drop_constraints: bool,
             logger: logging.Logger,
             max_distance: float=None,
             access_variant_id: int=None,
             max_access_distance: float=None,
             max_direct_walktime:float=None,
             air_distance_routing: bool=False,
             ):
        assert len(variant_ids) == 1
        transit_variant_id = variant_ids[0]
        transit_variant = ModeVariant.objects.get(id=transit_variant_id)
        access_variant = ModeVariant.objects.get(id=access_variant_id)
        dataframes = []
        try:
            queryset = self.get_filtered_queryset(variant_ids=variant_ids,
                                                  access_variant_id=access_variant_id,
                                                  place_ids=place_ids)
            logger.info('Berechne Zugangszeiten zu Haltestellen von '
                        f'{Mode(transit_variant.mode).name} mit '
                        f'{Mode(access_variant.mode).name}')
            max_distance_mode = float(max_access_distance or
                                      MODE_MAX_DISTANCE[access_variant.mode])

            if not place_ids:
                place_ids = Place.objects.values_list('id', flat=True)

            if air_distance_routing:
                df = self.calculate_airdistance_traveltimes(
                    access_variant=access_variant,
                    transit_variant_id=transit_variant.id,
                    max_distance=max_distance_mode,
                    place_ids=place_ids,
                    logger=logger,
                )
                df.rename(columns={'variant_id': 'access_variant_id',}, inplace=True)
                dataframes.append(df)
            else:
                chunk_size = 100
                for i in range(0, len(place_ids), chunk_size):
                    place_part = place_ids[i:i + chunk_size]
                    df = self.calc_routed_traveltimes(
                        access_variant,
                        transit_variant=transit_variant,
                        max_distance=max_distance_mode,
                        logger=logger,
                        place_ids=place_part)
                    df.rename(columns={'variant_id': 'access_variant_id',}, inplace=True)

                    dataframes.append(df)
                    logger.info(f'{min((i+chunk_size), len(place_ids)):n}/'
                                f'{len(place_ids):n} Orten berechnet')

            if not dataframes:
                msg = 'Keine Routen gefunden'
                raise RoutingError(msg)
            else:
                df = pd.concat(dataframes)
                df, ignore_columns = self.add_partition_key(
                    df,
                    transit_variant_id=transit_variant.pk,
                    place_ids=place_ids)
                self.write_results_to_database(logger,
                                               queryset,
                                               df,
                                               drop_constraints,
                                               ignore_columns=ignore_columns,
                                               )

        except RoutingError as err:
            msg = str(err)
            logger.error(msg)
            raise Exception(msg)
        else:
            logger.info('Berechnung der Reisezeitmatrizen erfolgreich abgeschlossen')

    @staticmethod
    def add_partition_key(df: pd.DataFrame,
                          transit_variant_id: int,
                          place_ids: List[int]) -> Tuple[pd.DataFrame, List[str]]:
        """add the partition key"""
        raise NotImplemented('To be defined in the subclass')


class MatrixCellStopRouter(AccessTimeRouterMixin):
    columns = ['stop_id', 'cell_id']
    partition_columns = ['transit_variant_id', 'access_variant_id']

    def get_filtered_queryset(self,
                              variant_ids: List[int],
                              access_variant_id: int,
                              stop_ids: List[int] = None,
                              **kwargs,
                              ) -> QuerySet:
        kwargs = {'stop_id__in': stop_ids, } if stop_ids else {}
        return MatrixCellStop.objects.filter(transit_variant_id__in=variant_ids,
                                             access_variant_id=access_variant_id,
                                             **kwargs)

    def get_sources(self,
                    stops: List[int] = [],
                    transit_variant:int = None,
                    **kwargs):
        if not transit_variant:
            transit_variant = ModeVariant.objects.filter(mode=Mode.TRANSIT).first()
        sources = Stop.objects.filter(variant=transit_variant)
        if stops:
            sources = sources.filter(id__in=stops)
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

    def get_airdistance_query(self,
                              speed: float,
                              max_distance: float,
                              access_variant_id: int,
                              transit_variant_id: int,
                              **kwargs) -> str:
        """
        returns a query and its parameters to calculate the air distance
        Parameters
        ----------
        speed: float
        max_distance: float
        variant: int: the transit-variant of the stops

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
        %s AS variant_id,
        %s AS transit_variant_id,
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
        FROM "{stop_tbl}" AS s
        WHERE s.variant_id = %s) AS s
        WHERE c.id = r.cell_id
        AND st_dwithin(c."pnt", s."geom", %s * s.kf)
        '''
        params = (access_variant_id,
                  transit_variant_id,
                  speed,
                  transit_variant_id,
                  max_distance)
        return query, params

    @staticmethod
    def add_partition_key(df: pd.DataFrame,
                          transit_variant_id: int,
                          **kwargs) -> Tuple[pd.DataFrame, List[str]]:
        """add the partition key"""
        df['transit_variant_id'] = transit_variant_id
        ignore_columns = []
        return df, ignore_columns


class MatrixPlaceStopRouter(AccessTimeRouterMixin):
    columns = ['place_id', 'stop_id']
    partition_columns = ['partition_id']

    def get_filtered_queryset(self,
                              variant_ids: List[int],
                              access_variant_id: int,
                              place_ids: List[int] = None,
                              **kwargs) -> QuerySet:
        qs = MatrixPlaceStop.objects.filter(stop__variant_id__in=variant_ids,
                                            access_variant_id=access_variant_id)
        if place_ids:
            qs = qs.filter(place_id__in=place_ids)
        return qs

    def get_sources(self, place_ids, **kwargs) -> Place:
        sources = Place.objects.all()
        if place_ids:
            sources = sources.filter(id__in=place_ids)
        sources = sources\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs',function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs',function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return sources

    def get_destinations(self, transit_variant, **kwargs) -> Stop:
        destinations = Stop.objects.filter(variant_id=transit_variant)\
            .annotate(wgs=Transform('geom', 4326))\
            .annotate(lat=Func('wgs', function='ST_Y', output_field=FloatField()),
                      lon=Func('wgs', function='ST_X', output_field=FloatField()))\
            .values('id', 'lon', 'lat')
        return destinations

    def get_airdistance_query(self,
                              speed: float,
                              max_distance: float,
                              access_variant_id:int,
                              transit_variant_id:int,
                              place_ids: List[int] = [],
                              **kwargs,
                              ) -> Tuple[str, tuple]:
        """
        returns a query and its parameters to calculate the air distance
        Parameters
        ----------
        speed: float
        max_distance: float
        transit_variant_id: int: the transit-variant of the stops
        place_ids: List[int], optional

        Returns
        -------
        query: sql
        params: tuple
        """

        place_tbl = Place._meta.db_table
        stop_tbl = Stop._meta.db_table

        place_ids = self.get_sources(place_ids=place_ids)
        p_places = list(place_ids.values_list('id', flat=True))

        query = f'''SELECT
        p.id AS place_id,
        s.id AS stop_id,
        %s AS variant_id,
        ARRAY[%s, p.infrastructure_id] AS partition_id,
        st_distance(p."pnt_25832", p."pnt_25832") / %s * (6.0/1000) AS minutes
        FROM
        (SELECT
        s.id,
        s.geom,
        st_transform(s.geom, 25832) AS pnt_25832
        FROM "{stop_tbl}" AS s
        WHERE s.variant_id = %s) AS s,
        (SELECT p.id,
        p.geom,
        st_transform(p.geom, 25832) AS pnt_25832,
        cosd(st_y(st_transform(p.geom, 4326))) AS kf,
        p.infrastructure_id
        FROM "{place_tbl}" AS p
        WHERE p.id = ANY(%s)) AS p
        WHERE st_dwithin(s."geom", p."geom", %s * p.kf)
        '''
        params = (access_variant_id,
                  transit_variant_id,
                  speed,
                  transit_variant_id,
                  p_places,
                  max_distance)
        return query, params

    @staticmethod
    def add_partition_key(df: pd.DataFrame,
                          transit_variant_id: int,
                          place_ids: List[int]) -> Tuple[pd.DataFrame, List[str]]:
        """add the partition key"""
        df['transit_variant_id'] = transit_variant_id

        # add infrastructure_id
        places_infra = pd.DataFrame(Place.objects.filter(id__in=place_ids)
                                    .values('id', 'infrastructure_id'))\
            .rename(columns={'id': 'place_id'},)\
            .set_index('place_id')

        df = df.merge(places_infra, right_index=True, left_on='place_id')
        def make_partition_key(row):
            return f"{{{row['transit_variant_id']:0.0f},{row['infrastructure_id']:0.0f}}}"
        df['partition_id'] = df.apply(make_partition_key, axis=1)

        ignore_columns = ['transit_variant_id',
                          'infrastructure_id']

        return df, ignore_columns
