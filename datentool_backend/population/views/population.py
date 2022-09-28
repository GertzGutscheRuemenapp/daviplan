import pandas as pd
import math
from io import StringIO
from django.http.request import QueryDict
from django_filters import rest_framework as filters
from django.db.models import Max, Min
from drf_spectacular.utils import (extend_schema,
                                   OpenApiResponse,
                                   inline_serializer)
from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response

from datentool_backend.utils.views import ProtectCascadeMixin, ExcelTemplateMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.utils.pop_aggregation import (
    intersect_areas_with_raster, aggregate_population, aggregate_many,
    disaggregate_population)
from datentool_backend.utils.regionalstatistik import Regionalstatistik
from datentool_backend.population.models import (
    PopulationRaster,
    Prognosis,
    Population,
    PopulationEntry,
    RasterCellPopulationAgeGender,
    AreaCell,
    Year
    )
from datentool_backend.demand.constants import RegStatAgeGroups, regstatgenders
from datentool_backend.demand.models import AgeGroup
from datentool_backend.utils.serializers import (MessageSerializer,
                                                 use_intersected_data,
                                                 drop_constraints,
                                                 area_level)
from datentool_backend.utils.processes import (ProtectedProcessManager,
                                               ProcessScope)
from datentool_backend.population.serializers import (
    PrognosisSerializer, PopulationSerializer, PopulationDetailSerializer,
    PopulationEntrySerializer, PopulationTemplateSerializer,
    prognosis_id_serializer, area_level_id_serializer, years_serializer)
from datentool_backend.site.models import SiteSetting
from datentool_backend.area.models import Area, AreaLevel

import logging

logger = logging.getLogger('population')


class PrognosisViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Prognosis.objects.all()
    serializer_class = PrognosisSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationFilter(filters.FilterSet):
    is_prognosis = filters.BooleanFilter(field_name='prognosis',
                                         lookup_expr='isnull', exclude=True)
    class Meta:
        model = Population
        fields = ['is_prognosis']


class PopulationViewSet(viewsets.ModelViewSet):
    queryset = Population.objects.all()
    serializer_class = PopulationSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_class = PopulationFilter

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
        drop_constraints = request.data.get('drop_constraints', False)

        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

            #  set new query-params
            old_data = self.request.data
            data = QueryDict(mutable=True)
            data.update(self.request.data)
            data['drop_constraints'] = False
            request._full_data = data

            use_intersected_data = request.data.get('use_intersected_data', False)
            pop_rasters = PopulationRaster.objects.all()
            for pop_raster in pop_rasters:
                for area_level in AreaLevel.objects.all():
                    areas = Area.objects.filter(area_level=area_level)
                    cells = AreaCell.objects.filter(area__in=areas)
                    if not areas or (cells and use_intersected_data):
                        continue
                    intersect_areas_with_raster(areas, pop_raster=pop_raster)

            #data['use_intersected_data'] = 'True'
            #request._full_data = data

            for population in Population.objects.all():
                disaggregate_population(population=population,
                                        use_intersected_data=True,
                                       drop_constraints=drop_constraints)
                #self.disaggregate(request, **{'pk': population.id})

            # restore the data
            #request._request.GET = old_data

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

        use_intersected_data = request.data.get('use_intersected_data', False)
        drop_constraints = request.data.get('drop_constraints', 'False')
        msg = disaggregate_population(
            population, use_intersected_data=use_intersected_data,
            drop_constraints=drop_constraints)
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

        drop_constraints = request.data.get('drop_constraints', False)
        area_level = AreaLevel.objects.get(id=request.data.get('area_level'))
        aggregate_population(area_level, population,
                             drop_constraints=drop_constraints)

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
        drop_constraints = request.data.get('drop_constraints', False)

        aggregate_many(AreaLevel.objects.all(), Population.objects.all(),
                       drop_constraints=drop_constraints)

        msg = 'Aggregations of all Populations were successful.'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(description='Pull population data in default statistics level '
                   'for all available years from Regionalstatistik GENESIS API. '
                   'ALL EXISTING POPULATION DATA WILL BE DELETED!',
                   request=inline_serializer(
                       name='PullPopulationSerializer',
                       fields={'drop_constraints': drop_constraints,},
                       ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Pull successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Not Acceptable'),
                              500: OpenApiResponse(MessageSerializer,
                                                   'Pull failed')})
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def pull_regionalstatistik(self, request, **kwargs):
        with ProtectedProcessManager(request.user,
                                     scope=ProcessScope.POPULATION):
            logger.info('Frage Bevölkerungsdaten von der Regionalstatistik ab.')
            CHUNK_SIZE = 10
            age_groups = AgeGroup.objects.all()
            if not RegStatAgeGroups.check(age_groups):
                msg = ('Die Altersklassen stimmen nicht mit '
                       'denen der Regionalstatistik überein')
                logger.error(msg)
                return Response({'message': msg},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
            # ToDo: there is also is_default_pop_level. set is_default_pop_level
            # automatically to the is_statistic_level level on completion
            # or complain here with 406 if they are not the same atm?
            try:
                area_level = AreaLevel.objects.get(is_statistic_level=True)
            except AreaLevel.DoesNotExist:
                msg = 'Keine Gebietseinheit für die Statistiken definiert'
                logger.error(msg)
                return Response({'message': msg},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

            areas = Area.annotated_qs(area_level).filter(area_level=area_level)

            min_max_years = Year.objects.all().aggregate(Min('year'), Max('year'))
            settings = SiteSetting.load()
            username = settings.regionalstatistik_user or None
            password = settings.regionalstatistik_password or None
            api = Regionalstatistik(start_year=min_max_years['year__min'],
                                    end_year=min_max_years['year__max'],
                                    username=username,
                                    password=password)
            logger.info(f'Jahre {min_max_years["year__min"]} bis '
                        f'{min_max_years["year__max"]} angefragt')
            ags_list = areas.values_list('ags', flat=True)
            frames = []
            try:
                chunks = math.ceil(len(ags_list) / CHUNK_SIZE)
                for i in range(0, chunks):
                    j = i * CHUNK_SIZE
                    k = min(j+CHUNK_SIZE, len(ags_list))
                    ags = ags_list[j:k]
                    frames.append(api.query_population(ags=ags))
                    logger.info(f'{k}/{len(ags_list)} Gebiete abgefragt')
            except PermissionDenied as e:
                msg = ('Die Datenmenge ist zu groß, um sie ohne Konto bei der '
                'Regionalstatistik abrufen zu können. Bitte benachrichtigen Sie '
                'den/die Toolkoordinator/in, dass ein Konto beantragt und die '
                'Zugangsdaten in den Grundeinstellungen von daviplan eingetragen '
                'werden müssen. Falls dort bereits ein Konto eingetragen ist, '
                'überprüfen Sie bitte die Gültigkeit der Zugangsdaten.')
                logger.error(msg)
                return Response({'message': msg, },
                                status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                logger.error(str(e))
                return Response({'message': str(e),},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            df_population = pd.concat(frames)
            years = df_population['year'].unique()
            years.sort()
            logger.info('Bevölkerungsdaten für die Jahre '
                        f'{", ".join(years.astype("str"))} gefunden')
            logger.info('Verarbeite Bevölkerungsdaten')
            regstatagegroups = RegStatAgeGroups.as_series()
            area_ids = pd.DataFrame(
                areas.values('id', 'ags')).set_index('ags').loc[:, 'id']
            area_ids.name = 'area_id'

            year_grouped = df_population.groupby('year')
            year2population = {}
            populations = []
            for y, year_group in year_grouped:
                try:
                    year = Year.objects.get(year=y)
                except Year.DoesNotExist:
                    continue
                # delete existing population and all depending objects
                try:
                    population = Population.objects.get(year=year, prognosis=None)
                    population.delete()
                except Population.DoesNotExist:
                    pass
                # (Re-)Create Population
                population = Population.objects.create(year=year, prognosis=None)
                populations.append(population)
                year2population[year.year] = population.id

            y2p = pd.Series(year2population, name='population_id')
            # add gender_id, agegroup_id, area_id and population_id
            df_population = df_population\
                .merge(regstatgenders, left_on='GES', right_index=True)\
                .merge(regstatagegroups, left_on='ALTX20', right_index=True)\
                .merge(area_ids, left_on='AGS', right_index=True)\
                .merge(y2p, left_on='year', right_index=True)\
                .rename(columns={'inhabitants': 'value', })\
                .loc[:, ['population_id', 'area_id', 'gender_id', 'age_group_id', 'value']]

            drop_constraints = request.data.get('drop_constraints', True)

            logger.info('Schreibe Bevölkerungsdaten in Datenbank')
            with StringIO() as file:
                df_population.to_csv(file, index=False)
                file.seek(0)
                PopulationEntry.copymanager.from_csv(
                    file,
                    drop_constraints=drop_constraints, drop_indexes=drop_constraints,
                )
            logger.info('Disaggregiere Bevölkerungsdaten')
            for i, population in enumerate(populations):
                disaggregate_population(population, use_intersected_data=True,
                                        drop_constraints=drop_constraints)
                logger.info(f'{i + 1}/{len(populations)}')
            logger.info('Aggregiere Bevölkerungsdaten')
            aggregate_many(AreaLevel.objects.all(), populations,
                           drop_constraints=drop_constraints)
            msg = ('Abfrage der Bevölkerungsdaten von der Regionalstatistik '
                   'erfolgreich')
            logger.info(msg)
            return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


class PopulationEntryViewSet(ExcelTemplateMixin, viewsets.ModelViewSet):
    queryset = PopulationEntry.objects.all()
    serializer_class = PopulationEntrySerializer
    serializer_action_classes = {'create_template': PopulationTemplateSerializer,
                                 'upload_template': PopulationTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_fields = ['population']

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

    @action(methods=['POST'], detail=False,
            parser_classes=[CamelCaseMultiPartParser])
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        with ProtectedProcessManager(request.user,
                                     scope=ProcessScope.POPULATION):
            return super().upload_template(request)