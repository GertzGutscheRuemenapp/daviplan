import logging
logger = logging.getLogger('routing')

import pandas as pd
import numpy as np
from typing import List, Tuple
from io import StringIO


from django.db import transaction, connection
from django.db.models.query import QuerySet
from django.db.models import FloatField
from django.contrib.gis.db.models.functions import Transform, Func

from rest_framework import status

from datentool_backend.utils.routers import OSRMRouter

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
                                            )



class RoutingError(Exception):
    """A Routing Error"""


class TravelTimeRouterMixin:
    columns: List[str] = []

    def calc(self,
             variant_ids: List[int],
             places: List[int],
             drop_constraints: bool,
             logger: logging.Logger,
             max_distance: float=None,
             access_variant_id: int=None,
             max_access_distance: float=None,
             max_direct_walktime: float=None,
             air_distance_routing: bool=False,
             ):
        variants = [ModeVariant.objects.get(pk=vid) for vid in variant_ids] \
            or ModeVariant.objects.all()
        dataframes = []
        try:
            queryset = self.get_filtered_queryset(variants=variants,
                                                  places=places)
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
                        access_variant = ModeVariant.objects.get(mode=Mode.WALK)

                    max_access_distance = float(max_access_distance or
                                                MODE_MAX_DISTANCE[variant.mode])
                    max_direct_walktime = float(max_direct_walktime or
                                                DEFAULT_MAX_DIRECT_WALKTIME)

                    df = self.prepare_and_calc_transit_traveltimes(
                        logger,
                        access_variant,
                        places,
                        max_access_distance,
                        drop_constraints,
                        variant,
                        max_direct_walktime,
                    )
                    dataframes.append(df)
                else:
                    if air_distance_routing:
                        df = self.calculate_airdistance_traveltimes(
                            variant,
                            max_distance=max_distance_mode,
                            places=places,
                            logger=logger,
                        )
                        dataframes.append(df)
                    else:
                        if not places:
                            places = Place.objects.values_list('id', flat=True)
                        chunk_size = 100
                        for i in range(0, len(places), chunk_size):
                            place_part = places[i:i+chunk_size]
                            df = self.calc_routed_traveltimes(
                                variant,
                                max_distance=max_distance_mode,
                                logger=logger,
                                places=place_part)
                            dataframes.append(df)
                            logger.info(f'{min((i+chunk_size), len(places))}/'
                                        f'{len(places)} Orte berechnet')

            if not dataframes:
                msg = 'Keine Routen gefunden'
                raise RoutingError(msg)
            else:
                df = pd.concat(dataframes)
                logger.info('Schreibe Ergebnisse in die Datenbank')
                success, msg = self.save_df(df, queryset, drop_constraints)
                if not success:
                    raise RoutingError(msg)

        except RoutingError as err:
            ret_status = status.HTTP_406_NOT_ACCEPTABLE
            msg = str(err)
            logger.error(msg)
        else:
            ret_status = status.HTTP_202_ACCEPTED
            logger.info(msg)
            logger.info('Berechnung der Reisezeitmatrizen erfolgreich abgeschlossen')

    def prepare_and_calc_transit_traveltimes(self,
                                             logger: logging.Logger,
                                             access_variant: ModeVariant,
                                             places: List[int],
                                             max_distance: float,
                                             drop_constraints: bool,
                                             variant: ModeVariant,
                                             max_direct_walktime: float,
                                             ) -> pd.DataFrame:
        # calculate time from place to stop
        matrix_place_stop = MatrixPlaceStopRouter()
        df_ps = matrix_place_stop.calc_routed_traveltimes(
            variant=access_variant,
            places=places,
            max_distance=max_distance,
            logger=logger,
        )
        qs = matrix_place_stop.get_filtered_queryset(
            variants=[access_variant.pk],
            places=places)
        success, msg = matrix_place_stop.save_df(df_ps, qs, drop_constraints)
        if not success:
            raise RoutingError(msg)

        # calculate time from stop to cell
        matrix_cell_stop = MatrixCellStopRouter()
        stops = Stop.objects.values_list('id', flat=True)
        chunk_size = 100
        dataframes_cs = []

        for i in range(0,  len(stops),  chunk_size):
            stops_part = stops[i:i + chunk_size]
            df_cs = matrix_cell_stop.calc_routed_traveltimes(
                variant=access_variant,
                max_distance=max_distance,
                stops=stops_part,
                logger=logger,
            )
            dataframes_cs.append(df_cs)
        df_cs = pd.concat(dataframes_cs)

        qs = matrix_cell_stop.get_filtered_queryset(
            variants=[access_variant.pk])
        success, msg = matrix_cell_stop.save_df(df_cs, qs, drop_constraints)
        if not success:
            raise RoutingError(msg)

        logger.debug(msg)
        df = self.calculate_transit_traveltime(
            access_variant=access_variant,
            transit_variant=variant,
            places=places,
            max_direct_walktime=max_direct_walktime,
        )
        return df

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

        sources = sources.order_by('id')
        destinations = destinations.order_by('id')

        source_coords = list(sources.values_list('lon', 'lat', named=False))
        dest_coords = list(destinations.values_list('lon', 'lat', named=False))

        matrix = router.matrix_calculation(source_coords, dest_coords)

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
        logger.debug(df)
        return df

    @staticmethod
    def save_df(df: pd.DataFrame,
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
            msg = (f'Berechnung der Reisezeiten erfolgreich, {n_deleted} Einträge '
                   f'entfernt und {len(df)} Einträge hinzugefügt '
                   f'({model._meta.object_name})')
            return (True, msg)

    def get_filtered_queryset(variants: List[int], **kwargs) -> QuerySet:
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

        sources = self.get_sources(**kwargs).order_by('id')
        destinations = self.get_destinations(**kwargs).order_by('id')

        return self.route(variant,
                          sources,
                          destinations,
                          logger,
                          max_distance=max_distance,
                          id_columns=self.columns)

    def calculate_airdistance_traveltimes(self,
                                          variant: ModeVariant,
                                          max_distance: float,
                                          logger: logging.Logger,
                                          **kwargs) -> pd.DataFrame:
        """calculate traveltimes"""
        logger.info('start calculation of air-distance matrix')
        speed = MODE_SPEED[variant.mode]

        query, params = self.get_airdistance_query(speed=speed,
                                                   max_distance=max_distance,
                                                   **kwargs)

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = self.columns + ['minutes']
            df = pd.DataFrame(cursor.fetchall(),
                              columns=columns)

        logger.info('calculation of air-distance matrix finished')

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


class MatrixCellPlaceRouter(TravelTimeRouterMixin):
    columns = ['place_id', 'cell_id']

    def get_filtered_queryset(self,
                              variants: List[int],
                              places: List[int] = None,
                              **kwargs) -> QuerySet:
        qs = MatrixCellPlace.objects.filter(variant_id__in=variants)
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
        cosd(st_y(st_transform(p.geom, 4326))) AS kf
        FROM "{place_tbl}" AS p
        WHERE p.id = ANY(%s)) AS p
        WHERE c.id = r.cell_id
        AND st_dwithin(c."pnt", p."geom", %s / p.kf)
        '''

        params = (speed, p_places, max_distance)

        return query, params


class MatrixCellStopRouter(TravelTimeRouterMixin):
    columns = ['stop_id', 'cell_id']

    def get_filtered_queryset(self, variants: List[int], **kwargs) -> QuerySet:
        return MatrixCellStop.objects.filter(variant_id__in=variants)

    def get_sources(self,
                    stops: List[int] = [],
                    **kwargs):
        sources = Stop.objects.all()
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


class MatrixPlaceStopRouter(TravelTimeRouterMixin):
    columns = ['place_id', 'stop_id']

    def get_filtered_queryset(self,
                              variants: List[int],
                              places: List[int] = None,
                              **kwargs) -> QuerySet:
        qs = MatrixPlaceStop.objects.filter(variant_id__in=variants)
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