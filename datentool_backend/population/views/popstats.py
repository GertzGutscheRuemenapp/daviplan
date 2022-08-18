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

from datentool_backend.utils.processes import ProtectedProcessManager
from datentool_backend.utils.serializers import (MessageSerializer,
                                                 drop_constraints,
                                                 )

from datentool_backend.population.serializers import (PopStatisticSerializer,
                                                      PopStatEntrySerializer,
                                                      )
from datentool_backend.site.models import SiteSetting
from datentool_backend.area.models import Area, AreaLevel


class PopStatisticViewSet(viewsets.ModelViewSet):
    queryset = PopStatistic.objects.all()
    serializer_class = PopStatisticSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_fields = ['year']

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
        with ProtectedProcessManager(request.user):
            min_max_years = Year.objects.all().aggregate(Min('year'), Max('year'))
            settings = SiteSetting.load()
            username = settings.regionalstatistik_user or None
            password = settings.regionalstatistik_password or None
            api = Regionalstatistik(start_year=min_max_years['year__min'],
                                    end_year=min_max_years['year__max'],
                                    username=username,
                                    password=password)
            try:
                area_level = AreaLevel.objects.get(is_statistic_level=True)
            except AreaLevel.DoesNotExist:
                msg = 'No AreaLevel for statistics defined'
                return Response({'message': msg, },
                                status=status.HTTP_406_NOT_ACCEPTABLE)

            areas = Area.annotated_qs(area_level).filter(area_level=area_level)
            ags = areas.values_list('ags', flat=True)
            try:
                df_births = api.query_births(ags=ags)
                df_deaths = api.query_deaths(ags=ags)
                df_migration = api.query_migration(ags=ags)
            except PermissionDenied as e:
                return Response({'message': str(e), },
                                status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({'message': str(e), },
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

            drop_constraints = request.data.get('drop_constraints', True)

            with StringIO() as file:
                df_popstat.to_csv(file, index=False)
                file.seek(0)
                PopStatEntry.copymanager.from_csv(
                    file,
                    drop_constraints=drop_constraints, drop_indexes=drop_constraints,
                )
            msg = 'Download of Population Statistics from Regionalstatistik successful'
            return Response({'message': msg, }, status=status.HTTP_202_ACCEPTED)


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
