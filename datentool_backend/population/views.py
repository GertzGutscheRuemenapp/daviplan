import pandas as pd
from io import StringIO
from distutils.util import strtobool
from django.http.request import QueryDict
from django.db import connection
from django_filters import rest_framework as filters
from django.db.models import Max, Min
from drf_spectacular.utils import (extend_schema,
                                   OpenApiResponse,
                                   inline_serializer)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db import transaction
from django.db.models import Max, Sum

from datentool_backend.utils.views import ProtectCascadeMixin, ExcelTemplateMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.area.views import intersect_areas_with_raster
from .regionalstatistik import Regionalstatistik
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
                     Year
                     )
from datentool_backend.demand.constants import RegStatAgeGroups
from datentool_backend.demand.models import AgeGroup

from datentool_backend.utils.serializers import (MessageSerializer,
                                                 use_intersected_data,
                                                 drop_constraints,
                                                 area_level,
                                                 )

from datentool_backend.population.serializers import (RasterSerializer,
                                                      PopulationRasterSerializer,
                                                      PrognosisSerializer,
                                                      PopulationSerializer,
                                                      PopulationDetailSerializer,
                                                      PopulationEntrySerializer,
                                                      PopStatisticSerializer,
                                                      PopStatEntrySerializer,
                                                      PopulationTemplateSerializer,
                                                      prognosis_id_serializer,
                                                      area_level_id_serializer,
                                                      years_serializer,
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

    @extend_schema(description='Disaggregate all Populations',
                   request=inline_serializer(
                       name='DisaggregateAllPopulationsSerializer',
                       fields={
                           'use_intersected_data': use_intersected_data,
                           'drop_constraints': drop_constraints,
                       }
                   ),
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

            use_intersected_data = bool(strtobool(
                request.data.get('use_intersected_data', 'False')))
            pop_rasters = PopulationRaster.objects.all()
            for pop_raster in pop_rasters:
                for area_level in AreaLevel.objects.all():
                    areas = Area.objects.filter(area_level=area_level)
                    cells = AreaCell.objects.filter(area__in=areas)
                    if not areas or (cells and use_intersected_data):
                        continue
                    intersect_areas_with_raster(areas, pop_raster=pop_raster)

            data['use_intersected_data'] = 'True'
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
                   request=inline_serializer(
                       name='DisaggregatePopulationSerializer',
                       fields={
                           'area_level': area_level,
                           'use_intersected_data': use_intersected_data,
                           'drop_constraints': drop_constraints,
                       }
                   ),
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
        if ac and bool(strtobool(request.data.get('use_intersected_data', 'False'))):
            msg = 'use precalculated rastercells\n'
        else:
            intersect_areas_with_raster(Area.objects.filter(id__in=areas),
                                        pop_raster=population.popraster)
            msg = f'{len(areas)} Areas intersected with Rastercells.\n'
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
                   request=inline_serializer(
                       name='AggregatePopulationAreaSerializer',
                       fields={
                           'area_level': area_level,
                           'use_intersected_data': use_intersected_data,
                           'drop_constraints': drop_constraints
                       }
                   ),
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
                   request=inline_serializer(
                       name='AggregateAllPopulationsSerializer',
                       fields={
                           'use_intersected_data': use_intersected_data,
                           'drop_constraints': drop_constraints,
                       }
                   ),
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
                entries = AreaPopulationAgeGender.objects.filter(
                    area__area_level=area_level)
                summed_values = entries.values(
                    'population__year', 'area', 'population__prognosis')\
                    .annotate(Sum('value'))
                max_value = summed_values.aggregate(
                    Max('value__sum'))['value__sum__max']
                area_level.max_population = max_value
                area_level.population_cache_dirty = False
                area_level.save()

            # restore the data
            request._full_data = old_data

            if drop_constraints:
                manager.restore_constraints()
                manager.restore_indexes()

        msg = 'Aggregations of all Populations were successful.'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(description='Pull population data in default statistics level '
                   'for all available years from Regionalstatistik GENESIS API. '
                   'ALL EXISTING POPULATION DATA WILL BE DELETED!',
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Pull successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Not Acceptable'),
                              500: OpenApiResponse(MessageSerializer,
                                                   'Pull failed')})
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def pull_regionalstatistik(self, request, **kwargs):

        age_groups = AgeGroup.objects.all()
        if not RegStatAgeGroups.check(age_groups):
            return Response({'message': 'Die Altersklassen stimmen nicht mit '
                             'denen der Regionalstatistik überein'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        min_max_years = Year.objects.all().aggregate(Min('year'), Max('year'))
        # ToDo: username, password for bigger data?
        api = Regionalstatistik(start_year=min_max_years['year__min'],
                                end_year=min_max_years['year__max'])
        ags = [a.attributes.get(field__name='ags').value
               for a in Area.objects.all()]
        try:
            df_population = api.query_population(ags=ags)
        except Exception as e:
            return Response({'message': str(e),},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # ToDo: what to delete?
        # Population.objects.all().delete()
        year_grouped = df_population.groupby('year')
        for y, year_group in year_grouped:
            try:
                year = Year.objects.get(year=y)
            except Year.DoesNotExist:
                continue
            # ToDo: create Population (?)
            # Population.objects.create()
            ag_grouped = year_group.groupby('ALTX20')
            for ag, ag_group in ag_grouped:
                reg_ag = RegStatAgeGroups.get(ag)
                # should actually not happen unless Regionalstatistik changes
                # the age groups or codes (throw exception?)
                if not reg_ag:
                    continue
                # should be in, was checked at the beginning
                age_group = AgeGroup.objects.get(from_age=reg_ag.from_age,
                                                 to_age=reg_ag.to_age)
                # ToDo:create PopEntry per agegroup, gender and area
                raise NotImplementedError


class PopulationEntryViewSet(ExcelTemplateMixin, viewsets.ModelViewSet):
    queryset = PopulationEntry.objects.all()
    serializer_class = PopulationEntrySerializer
    serializer_action_classes = {'create_template': PopulationTemplateSerializer,
                                 'upload_template': PopulationTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    @extend_schema(description='Upload Population Template',
                   request=inline_serializer(
                       name='PopulationUploadTemplateSerializer',
                       fields={
                           'area_level': area_level_id_serializer,
                           'years': years_serializer,
                           'prognosis': prognosis_id_serializer,
                           'drop_constraints': drop_constraints
                       }
                       ),
                   )
    @action(methods=['POST'], detail=False, permission_classes=[CanEditBasedata])
    def create_template(self, request, **kwargs):
        area_level_id = request.data.get('area_level')
        prognosis_id = request.data.get('prognosis')
        years = request.data.get('years')
        return super().create_template(request,
                                       area_level_id=area_level_id,
                                       years=years,
                                       prognosis_id=prognosis_id,
                                       )



class PopStatisticViewSet(viewsets.ModelViewSet):
    queryset = PopStatistic.objects.all()
    serializer_class = PopStatisticSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_fields = ['year']


class PopStatEntryFilter(filters.FilterSet):
    year = filters.NumberFilter(field_name='popstatistic__year__year',
                                lookup_expr='exact')
    class Meta:
        model = PopStatEntry
        fields = ['popstatistic', 'year', 'area']


class PopStatEntryViewSet(viewsets.ModelViewSet):
    queryset = PopStatEntry.objects.all()
    serializer_class = PopStatEntrySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_class = PopStatEntryFilter
