import pandas as pd
from io import StringIO
from distutils.util import strtobool
from django.http.request import QueryDict
from django.db import connection

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db import transaction
from django.db.models import F, Max

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import (Raster,
                     PopulationRaster,
                     Prognosis,
                     Population,
                     PopulationEntry,
                     PopStatistic,
                     PopStatEntry,
                     RasterCellPopulationAgeGender,
                     RasterCellPopulation,
                     AreaPopulationAgeGender,
                     PopulationAreaLevel,
                     AreaCell,
                     )
from .serializers import (RasterSerializer,
                          PopulationRasterSerializer,
                          PrognosisSerializer,
                          PopulationSerializer,
                          PopulationDetailSerializer,
                          PopulationEntrySerializer,
                          PopStatisticSerializer,
                          PopStatEntrySerializer,
                          MessageSerializer,
                          )

from datentool_backend.area.models import Area, AreaLevel


class RasterViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Raster.objects.all()
    serializer_class = RasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationRasterViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PopulationRaster.objects.all()
    serializer_class = PopulationRasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PrognosisViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Prognosis.objects.all()
    serializer_class = PrognosisSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationViewSet(viewsets.ModelViewSet):
    queryset = Population.objects.all()
    serializer_class = PopulationSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    @extend_schema(description='return the population including the rastercellpopulationagegender_set',
                   responses=PopulationDetailSerializer)
    @action(methods=['GET'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def get_details(self, request, **kwargs):
        """
        route to return population with all entries
        """
        instance = self.get_object()
        serializer = PopulationDetailSerializer(instance)
        return Response(serializer.data)

    @extend_schema(description='intersect areas with rastercells',
                   parameters=[
                       OpenApiParameter(name='area_level', required=False, type=int,
        description='''if a specific area_level_id is provided,
        take this one instead of the areas of the population'''),
                       OpenApiParameter(name='drop_constraints',
                                        required=False,
                                        type=bool,
                                        default=True,
                                        description='set to false for tests')
                   ],
                   responses={202: OpenApiResponse(MessageSerializer, 'Intersection successful'),
                              406: OpenApiResponse(MessageSerializer, 'Intersection failed')})
    @action(methods=['POST'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def intersectareaswithcells(self, request, **kwargs):
        """
        route to intersect areas with raster cells
        """
        try:
            population: Population = self.queryset.get(**kwargs)
        except Population.DoesNotExist:
            msg = f'Population for {kwargs} not found'
            return Response({'message': msg,}, status.HTTP_406_NOT_ACCEPTABLE)

        # if a specific area-level is provided, take this one
        # instead of the areas of the population
        area_level_id = request.data.get('area_level')
        if area_level_id:
            areas = Area.objects.filter(area_level_id=area_level_id)\
                .values_list('pk', flat=True)
        else:
            areas = population.populationentry_set.distinct('area_id')\
                .values_list('area_id', flat=True)

        if not areas:
            return Response({'message': 'No areas available', },
                            status=status.HTTP_202_ACCEPTED)

        # use only cells with population and put values from Census to column pop
        raster_cells = population.popraster.raster.rastercell_set

        raster_cells_with_inhabitants = raster_cells\
            .filter(rastercellpopulation__isnull=False)\
            .annotate(pop=F('rastercellpopulation__value'),
                      rcp_id=F('rastercellpopulation__id'),
                      )

        # spatial intersect with areas from given area_level
        area_tbl = Area._meta.db_table

        rr = raster_cells_with_inhabitants.extra(
            select={f'area_id': f'"{area_tbl}".id',
                    f'm2_raster': 'st_area(st_transform(poly, 3035))',
                    f'm2_intersect': f'st_area(st_transform(st_intersection(poly, "{area_tbl}".geom), 3035))',
                    },
            tables=[area_tbl],
            where=[f'''st_intersects(poly, "{area_tbl}".geom)
            AND "{area_tbl}".id IN %s
            '''],
            params=(tuple(areas),),
        )

        df = pd.DataFrame.from_records(
            rr.values('id', 'area_id', 'pop', 'rcp_id',
                      'm2_raster', 'm2_intersect', 'cellcode'))\
            .set_index(['id', 'area_id'])

        df['share_area_of_cell'] = df['m2_intersect'] / df['m2_raster']

        # calculate weight as Census-Population *
        # share of area of the total area of the rastercell
        df['weight'] = df['pop'] * df['m2_intersect'] / df['m2_raster']

        # sum up the weights of all rastercells in an area
        area_weight = df['weight'].groupby(level='area_id').sum().rename('total_weight')

        # calculate the share of population, a rastercell
        # should get from the total population
        df = df.merge(area_weight, left_on='area_id', right_index=True)
        df['share_cell_of_area'] = df['weight'] / df['total_weight']

        # sum up the weights of all areas in a cell
        cell_weight = df['weight'].groupby(level='id').sum().rename('total_weight_cell')

        df = df.merge(cell_weight, left_on='id', right_index=True)
        df['share_area_of_cell'] = df['weight'] / df['total_weight_cell']

        df2 = df[['rcp_id', 'share_area_of_cell', 'share_cell_of_area']]\
            .reset_index()\
            .rename(columns={'rcp_id': 'cell_id'})[['area_id', 'cell_id', 'share_area_of_cell', 'share_cell_of_area']]

        ac = AreaCell.objects.filter(area__in=areas,
                                     cell__popraster=population.popraster)
        ac.delete()

        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with StringIO() as file:
            df2.to_csv(file, index=False)
            file.seek(0)
            AreaCell.copymanager.from_csv(file,
                drop_constraints=drop_constraints, drop_indexes=drop_constraints)

        msg = f'{len(areas)} Areas were successfully intersected with Rastercells.\n'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(description='Disaggregate all Populations',
                   parameters=[
                       OpenApiParameter(
                           name='use_intersected_data',
                           required=False, type=bool, default=True,
                           description='''use precalculated rastercells'''),
                       OpenApiParameter(name='drop_constraints',
                                        required=False,
                                        type=bool,
                                        default=True,
                                        description='set to false for tests'),
                   ],
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Disaggregation successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Disaggregation failed')})
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def disaggregateall(self, request, **kwargs):
        manager = RasterCellPopulationAgeGender.copymanager
        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

            #  set new query-params
            old_data = self.request.data
            data = QueryDict(mutable=True)
            data.update(self.request.data)
            data['drop_constraints'] = 'False'
            request._full_data = data

            for population in Population.objects.all():
                self.disaggregate(request, **{'pk': population.id})

            # restore the data
            request._request.GET = old_data

            if drop_constraints:
                manager.restore_constraints()
                manager.restore_indexes()

        msg = 'Disaggregations of all Populations were successful.'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(description='Disaggregate Population to rastercells',
                   parameters=[
                       OpenApiParameter(name='area_level', required=False, type=int,
        description='''if a specific area_level_id is provided,
        take this one instead of the areas of the population'''),
                       OpenApiParameter(name='use_intersected_data', required=False, type=bool,
        description='''use precalculated rastercells'''),
                       OpenApiParameter(name='drop_constraints',
                                        required=False,
                                        type=bool,
                                        default=True,
                                        description='set to false for tests'),
                   ],
                   responses={202: OpenApiResponse(MessageSerializer, 'Disaggregation successful'),
                              406: OpenApiResponse(MessageSerializer, 'Disaggregation failed')})
    @action(methods=['POST'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def disaggregate(self, request, **kwargs):
        """
        route to disaggregate the population to the raster cells
        """
        try:
            population: Population = self.queryset.get(**kwargs)
        except Population.DoesNotExist:
            msg = f'Population for {kwargs} not found'
            return Response({'message': msg,}, status.HTTP_406_NOT_ACCEPTABLE)

        areas = population.populationentry_set.distinct('area_id')\
            .values_list('area_id', flat=True)

        ac = AreaCell.objects.filter(area__in=areas,
                                     cell__popraster=population.popraster)

        # if rastercells are not intersected yet
        if ac and request.data.get('use_intersected_data'):
            msg = 'use precalculated rastercells\n'
        else:
            response = self.intersectareaswithcells(request, **kwargs)
            msg = response.data.get('message', '')
            ac = AreaCell.objects.filter(area__in=areas,
                                         cell__popraster=population.popraster)

        # get the intersected data from the database
        df_area_cells = pd.DataFrame.from_records(
            ac.values('cell__cell_id', 'area_id', 'share_cell_of_area'))\
            .rename(columns={'cell__cell_id': 'cell_id', })

        # take the Area population by age_group and gender
        entries = population.populationentry_set
        df_pop = pd.DataFrame.from_records(
            entries.values('area_id', 'gender_id', 'age_group_id', 'value'))

        # left join with the shares of each rastercell
        dd = df_pop.merge(df_area_cells,
                          on='area_id',
                          how='left')\
            .set_index(['cell_id', 'gender_id', 'age_group_id'])

        # areas without rastercells have no cell_id assigned
        cell_ids = dd.index.get_level_values('cell_id')
        has_no_rastercell = pd.isna(cell_ids)
        population_not_located = dd.loc[has_no_rastercell].value.sum()

        if population_not_located:
            areas_without_rastercells = Area.label_annotated_qs()\
                .filter(id__in=dd.loc[has_no_rastercell, 'area_id'])

            msg += f'{population_not_located} Inhabitants not located to rastercells in {areas_without_rastercells}\n'
        else:
            msg += 'all areas have rastercells with inhabitants\n'

        # can work only when rastercells are found
        dd = dd.loc[~has_no_rastercell]

        # population by age_group and gender in each rastercell
        dd.loc[:, 'pop'] = dd['value'] * dd['share_cell_of_area']

        # has to be summed up by rastercell, age_group and gender, because a rastercell
        # might have population from two areas
        df_cellagegender: pd.DataFrame = dd['pop']\
            .groupby(['cell_id', 'gender_id', 'age_group_id'])\
            .sum()\
            .rename('value')\
            .reset_index()

        df_cellagegender['cell_id'] = df_cellagegender['cell_id'].astype('i8')
        df_cellagegender['population_id'] = population.id

        # delete the existing entries
        # updating would leave values for rastercells, that do not exist any more
        rc_exist = RasterCellPopulationAgeGender.objects\
            .filter(population=population)
        rc_exist.delete()

        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with StringIO() as file:
            df_cellagegender.to_csv(file, index=False)
            file.seek(0)
            RasterCellPopulationAgeGender.copymanager.from_csv(
                file,
                drop_constraints=drop_constraints, drop_indexes=drop_constraints,
            )
        msg += f'Disaggregation of Population was successful.\n'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(description='Aggregate Population from rastercells to area',
                   parameters=[
                       OpenApiParameter(name='area_level', required=True, type=int,
        description='''The Area_level to aggregate to'''),
                       OpenApiParameter(name='use_intersected_data', required=False, type=bool,
        description='''use precalculated rastercells'''),
                       OpenApiParameter(name='drop_constraints',
                                        required=False,
                                        type=bool,
                                        default=True,
                                        description='set to false for tests'),
                   ],
                   responses={202: OpenApiResponse(MessageSerializer, 'Aggregation successful'),
                              406: OpenApiResponse(MessageSerializer, 'Aggregation failed')})
    @action(methods=['POST'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def aggregate_from_cell_to_area(self, request, **kwargs):
        """aggregate population from cell to area"""
        try:
            population: Population = self.queryset.get(**kwargs)
        except Population.DoesNotExist:
            msg = f'Population for {kwargs} not found'
            return Response({'message': msg, }, status.HTTP_406_NOT_ACCEPTABLE)

        area_level_id = request.data.get('area_level')
        acells = AreaCell.objects.filter(area__area_level_id=area_level_id)

        rasterpop = RasterCellPopulationAgeGender.objects.filter(population=population)
        rcp = RasterCellPopulation.objects.all()

        q_acells, p_acells = acells.values(
            'area_id', 'cell_id', 'share_area_of_cell').query.sql_with_params()
        q_pop, p_pop = rasterpop.values(
            'population_id', 'cell_id', 'value', 'age_group_id', 'gender_id')\
            .query.sql_with_params()
        q_rcp, p_rcp = rcp.values(
            'id', 'cell_id').query.sql_with_params()

        query = f'''SELECT
          p."population_id",
          ac."area_id",
          p."age_group_id",
          p."gender_id",
          SUM(p."value" * ac."share_area_of_cell") AS "value"
        FROM
          ({q_acells}) AS ac,
          ({q_pop}) AS p,
          ({q_rcp}) AS rcp
        WHERE ac."cell_id" = rcp."id"
        AND p."cell_id" = rcp."cell_id"
        GROUP BY p."population_id", ac."area_id", p."age_group_id", p."gender_id"
        '''

        params = p_acells + p_pop + p_rcp

        columns = ['population_id', 'area_id', 'age_group_id', 'gender_id', 'value']

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        df_areaagegender = pd.DataFrame(rows, columns=columns)

        ap_exist = AreaPopulationAgeGender.objects\
            .filter(population=population, area__area_level_id=area_level_id)
        ap_exist.delete()

        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with StringIO() as file:
            df_areaagegender.to_csv(file, index=False)
            file.seek(0)
            AreaPopulationAgeGender.copymanager.from_csv(
                file,
                drop_constraints=drop_constraints, drop_indexes=drop_constraints,
            )
        msg = f'Aggregation of Population was successful.\n'

        # validate_cache
        pop_arealevel, created = PopulationAreaLevel.objects.get_or_create(
            population=population,
            area_level_id=area_level_id)
        pop_arealevel.up_to_date = True
        pop_arealevel.save()

        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


    @extend_schema(description='Aggregate all Populations',
                   parameters=[
                       OpenApiParameter(
                           name='use_intersected_data',
                           required=False, type=bool, default=True,
                           description='''use precalculated rastercells'''),
                       OpenApiParameter(name='drop_constraints',
                                        required=False,
                                        type=bool,
                                        default=True,
                                        description='set to false for tests'),
                   ],
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Aggregation successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Aggregation failed')})
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def aggregateall_from_cell_to_area(self, request, **kwargs):
        manager = AreaPopulationAgeGender.copymanager
        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

            #  set new query-params
            old_data = self.request.data
            data = QueryDict(mutable=True)
            data.update(self.request.data)
            data['drop_constraints'] = 'False'
            request._full_data = data

            for area_level in AreaLevel.objects.all():
                for population in Population.objects.all():
                    data['area_level'] = area_level.id
                    self.aggregate_from_cell_to_area(request, **{'pk': population.id})
                max_value = AreaPopulationAgeGender.objects.filter(
                    area__area_level=area_level)\
                    .aggregate(Max('value'))
                area_level.max_population = max_value['value__max']
                area_level.population_cache_dirty = False
                area_level.save()

            # restore the data
            request._full_data = old_data

            if drop_constraints:
                manager.restore_constraints()
                manager.restore_indexes()

        msg = 'Aggregations of all Populations were successful.'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


class PopulationEntryViewSet(viewsets.ModelViewSet):
    queryset = PopulationEntry.objects.all()
    serializer_class = PopulationEntrySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopStatisticViewSet(viewsets.ModelViewSet):
    queryset = PopStatistic.objects.all()
    serializer_class = PopStatisticSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopStatEntryViewSet(viewsets.ModelViewSet):
    queryset = PopStatEntry.objects.all()
    serializer_class = PopStatEntrySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
