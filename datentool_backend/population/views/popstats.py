import pandas as pd
from io import StringIO
from django_filters import rest_framework as filters
from django.db.models import Max, Min
from drf_spectacular.utils import (extend_schema,
                                   OpenApiResponse,
                                   inline_serializer)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.utils.regionalstatistik import Regionalstatistik
from datentool_backend.population.models import (
    PopStatistic,
    PopStatEntry,
    Year
    )
from rest_framework.response import Response

from datentool_backend.utils.processes import (ProtectedProcessManager,
                                               ProcessScope)
from datentool_backend.utils.serializers import (MessageSerializer,
                                                 drop_constraints,
                                                 )

from datentool_backend.population.serializers import (PopStatisticSerializer,
                                                      PopStatEntrySerializer,
                                                      )
from datentool_backend.site.models import SiteSetting
from datentool_backend.area.models import Area, AreaLevel

import logging

logger = logging.getLogger('population')


class PopStatisticViewSet(viewsets.ModelViewSet):
    queryset = PopStatistic.objects.all()
    serializer_class = PopStatisticSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_fields = ['year']

    @extend_schema(description='Pull statistics (births, deaths, migration) '
                   'in default statistics level for all available years '
                   'from Regionalstatistik GENESIS API. '
                   'ALL EXISTING STATISTICS DATA WILL BE DELETED!',
                   request=inline_serializer(
                       name='PullPopStatSerializer',
                       fields={'drop_constraints': drop_constraints, },
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Pull successful'),
                              500: OpenApiResponse(MessageSerializer,
                                                   'Pull failed')})
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def pull_regionalstatistik(self, request, **kwargs):
        try:
            area_level = AreaLevel.objects.get(is_statistic_level=True)
        except AreaLevel.DoesNotExist:
            msg = 'Keine Gebietseinheit für Statistiken definiert'
            logger.error(msg)
            return Response({'message': msg, },
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        drop_constraints = request.data.get('drop_constraints', True)
        run_sync = request.data.get('sync', False)

        with ProtectedProcessManager(user=request.user,
                                     scope=ProcessScope.POPULATION) as ppm:
            if not run_sync:
                ppm.run_async(self._pull_regionalstatistik, area_level,
                              drop_constraints=drop_constraints)
            else:
                self._pull_regionalstatistik(area_level,
                                             drop_constraints=drop_constraints)

        return Response({
            'message': f'Abruf der Bevölkerungsstatistiken gestartet'
            }, status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def _pull_regionalstatistik(area_level: AreaLevel, drop_constraints=False):
        logger.info('Frage Bevölkerungsstatistiken von der '
                    'Regionalstatistik ab')
        min_max_years = Year.objects.all().aggregate(Min('year'), Max('year'))
        settings = SiteSetting.load()
        username = settings.regionalstatistik_user or None
        password = settings.regionalstatistik_password or None

        api = Regionalstatistik(start_year=min_max_years['year__min'],
                                end_year=min_max_years['year__max'],
                                username=username,
                                password=password)
        areas = Area.annotated_qs(area_level).filter(area_level=area_level)
        ags = areas.values_list('ags', flat=True)
        try:
            logger.info('Frage Geburtenstatistik ab')
            df_births = api.query_births(ags=ags)
            logger.info('Frage Sterbefälle ab')
            df_deaths = api.query_deaths(ags=ags)
            logger.info('Frage Migrationsstatistik ab')
            df_migration = api.query_migration(ags=ags)
        except PermissionDenied as e:
            logger.error(str(e))
            return
        except Exception as e:
            logger.error(str(e))
            return

        years = df_births['year'].unique()
        years.sort()
        logger.info('Statistiken für die Jahre '
                    f'{", ".join(years.astype("str"))} gefunden')
        logger.info('Verarbeite Statistiken')
        # ToDo: relying on provision of same years in all API responses
        # what if that is not the case
        year_grouped = df_births.groupby('year')
        year2popstatistic = {}
        for y, year_group in year_grouped:
            try:
                year = Year.objects.get(year=y)
            except Year.DoesNotExist:
                continue
            # delete existing popstatistics and all depending objects
            try:
                popstat = PopStatistic.objects.get(year=year)
                popstat.delete()
            except PopStatistic.DoesNotExist:
                pass
            # (Re-)Create PopStatistic
            popstat = PopStatistic.objects.create(year=year)
            year2popstatistic[year.year] = popstat.id

        y2p = pd.Series(year2popstatistic, name='popstatistic_id')

        area_ids = pd.DataFrame(areas.values('id', 'ags')).set_index('ags').loc[:, 'id']
        area_ids.name = 'area_id'

        df_popstat = df_births\
            .merge(df_deaths, on=['year', 'AGS'])\
            .merge(df_migration, on=['year', 'AGS'])\
            .merge(area_ids, left_on='AGS', right_index=True)\
            .merge(y2p, left_on='year', right_index=True)\
            .loc[:, ['popstatistic_id', 'area_id',
                     'births', 'deaths',
                     'immigration', 'emigration']]

        logger.info('Schreibe Statistiken in Datenbank')
        with StringIO() as file:
            df_popstat.to_csv(file, index=False)
            file.seek(0)
            PopStatEntry.copymanager.from_csv(
                file,
                drop_constraints=drop_constraints, drop_indexes=drop_constraints,
            )
        msg = ('Abfrage der Bevölkerungsstatistiken von der '
               'Regionalstatistik erfolgreich')
        logger.info(msg)

class PopStatEntryFilter(filters.FilterSet):
    year = filters.NumberFilter(field_name='popstatistic__year__year',
                                lookup_expr='exact')
    class Meta:
        model = PopStatEntry
        fields = ['popstatistic', 'year', 'area']


class PopStatEntryViewSet(viewsets.ModelViewSet):
    queryset = PopStatEntry.objects.select_related('popstatistic__year').all()
    serializer_class = PopStatEntrySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_class = PopStatEntryFilter
