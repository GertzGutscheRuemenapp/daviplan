import os
import logging

from rest_framework import viewsets
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Exists, OuterRef
from django.core.exceptions import BadRequest
from drf_spectacular.utils import (extend_schema, inline_serializer,
                                   OpenApiResponse)
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from djangorestframework_camel_case.parser import (CamelCaseMultiPartParser,
                                                   CamelCaseJSONParser)
from django.conf import settings

from datentool_backend.utils.views import SingletonViewSet, ProtectCascadeMixin
from datentool_backend.utils.routers import OSRMRouter
from datentool_backend.utils.serializers import MessageSerializer
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 HasAdminAccessOrReadOnlyAny,
                                                 CanEditBasedata)
from datentool_backend.modes.models import Mode
from datentool_backend.site.models import SiteSetting, ProjectSetting, Year
from datentool_backend.area.models import AreaLevel, Area
from datentool_backend.population.models import (PopulationRaster, Population,
                                                 PopStatistic)

from .serializers import (SiteSettingSerializer,
                          ProjectSettingSerializer,
                          BaseDataSettingSerializer,
                          YearSerializer,
                          MatrixStatisticsSerializer,
                          )
from datentool_backend.utils.processes import RunProcessMixin, ProcessScope
from datentool_backend.population.views.raster import PopulationRasterViewSet


class YearFilter(filters.FilterSet):
    active = filters.BooleanFilter(field_name='is_active')
    prognosis = filters.NumberFilter(field_name='population__prognosis')
    has_real_data = filters.BooleanFilter(field_name='has_real')
    has_prognosis_data = filters.BooleanFilter(field_name='has_prognosis')
    has_statistics_data = filters.BooleanFilter(field_name='has_statistics')
    class Meta:
        model = Year
        fields = ['is_real', 'is_prognosis', 'population__prognosis',
                  'has_real_data', 'has_prognosis_data']


class YearViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    serializer_class = YearSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_class = YearFilter

    def get_queryset(self):
        """ get the years. Request-parameters with_prognosis/with_population """
        all_years = Year.objects.all()

        pop_prognosis = Population.objects.filter(
            year=OuterRef('pk'), prognosis__isnull=False)
        pop_real = Population.objects.filter(
            year=OuterRef('pk'), prognosis__isnull=True)
        statistics = PopStatistic.objects.filter(year=OuterRef('pk'))

        qs = all_years.annotate(
            has_real=Exists(pop_real),
            has_prognosis=Exists(pop_prognosis),
            has_statistics=Exists(statistics)
        )
        return qs.order_by('year')

    @extend_schema(description='Set Year Range',
                   request=inline_serializer(
                       name='YearRangeSerializer',
                       fields={
                           'from_year': serializers.IntegerField(required=True),
                           'to_year': serializers.IntegerField(required=True),
                       }
                   ),
                   responses={
                       201: OpenApiResponse(YearSerializer(many=True)),
                       400: OpenApiResponse(MessageSerializer, 'Bad Request'),
                   }
                )
    @action(methods=['POST'], detail=False)
    def set_range(self, request):
        """create or delete years, if required"""
        try:
            from_year = int(request.data.get('from_year'))
            to_year = int(request.data.get('to_year'))
        except (ValueError, TypeError):
            raise BadRequest('from_year and to_year must be integers')
        if from_year > to_year:
            raise BadRequest('to_year has to be greater than or equal to '
                             f'{Year.MIN_YEAR}')
        if from_year < Year.MIN_YEAR:
            raise BadRequest(f'from_year has to be greater than {Year.MIN_YEAR}')

        years_to_delete = Year.objects.exclude(year__range=(from_year, to_year))
        years_to_delete.delete()

        for y in range(from_year, to_year+1):
            year = Year.objects.get_or_create(year=y)

        qs = Year.objects.all()
        data = self.serializer_class(qs, many=True).data

        return Response(data, status=status.HTTP_201_CREATED)

    @extend_schema(description='Set years for real population data',
                   request=inline_serializer(
                       name='RealYearSerializer',
                       fields={
                           'years': serializers.ListField(
                               child=serializers.IntegerField(),
                               required=True),
                       }
                   ),
                   responses={
                       201: OpenApiResponse(YearSerializer(many=True)),
                   }
                )
    @action(methods=['POST'], detail=False)
    def set_real_years(self, request):
        years = request.data.get('years', [])
        Year.objects.update(is_real=False)
        update_years = Year.objects.filter(year__in=years)
        update_years.update(is_real=True)
        return Response(self.serializer_class(update_years, many=True).data,
                        status=status.HTTP_201_CREATED)

    @extend_schema(description='Set years for population prognosis data',
                   request=inline_serializer(
                       name='PrognosisYearSerializer',
                       fields={
                           'years': serializers.ListField(
                               child=serializers.IntegerField(),
                               required=True),
                       }
                   ),
                   responses={
                       201: OpenApiResponse(YearSerializer(many=True)),
                   }
                )
    @action(methods=['POST'], detail=False)
    def set_prognosis_years(self, request):
        years = request.data.get('years', [])
        Year.objects.update(is_prognosis=False)
        update_years = Year.objects.filter(year__in=years)
        update_years.update(is_prognosis=True)
        return Response(self.serializer_class(update_years, many=True).data,
                        status=status.HTTP_201_CREATED)


class ProjectSettingViewSet(RunProcessMixin, SingletonViewSet):
    queryset = ProjectSetting.objects.all()
    model_class = ProjectSetting
    serializer_class = ProjectSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnlyAny]

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        if response.status_code == 200 and request.data.get('project_area'):

            msg_start = 'Verarbeitung des Planungsraums gestartet'
            msg_end = 'Verarbeitung des Planungsraums beendet'
            return self.run_sync_or_async(func=self._postprocess_project_area,
                                          user=request.user,
                                          scope=ProcessScope.AREAS,
                                          message_async=msg_start,
                                          message_sync=msg_end,
                                          ret_status=status.HTTP_200_OK)

        return response

    @staticmethod
    def _postprocess_project_area(logger: logging.Logger):
        logger.info('Verarbeitung des Planungsraums gestartet')
        for popraster in PopulationRaster.objects.all():
            logger.info('Verschneide Planungsraum mit dem Zensusraster...')
            PopulationRasterViewSet._intersect_census(
                popraster, drop_constraints=True)
        logger.info('Bereinige Daten:')
        for area_level in AreaLevel.objects.filter():
            areas = Area.objects.filter(area_level=area_level)
            if areas:
                logger.info(f'Lösche {len(areas):n} Gebiete der Ebene '
                            f'{area_level.name}...')
                areas.delete()
        logger.info('Entferne eventuell vorhandene Router...')
        # remove existing routers:
        fp_target_pbf = os.path.join(settings.MEDIA_ROOT, 'projectarea.pbf')
        # ToDo: default network?
        if os.path.exists(fp_target_pbf):
            try:
                os.remove(fp_target_pbf)
            except:
                pass
        for mode in [Mode.WALK, Mode.BIKE, Mode.CAR]:
            router = OSRMRouter(mode)
            if router.service_is_up:
                router.remove()
        logger.info('Verarbeitung des Planungsraums abgeschlossen.')


class BaseDataSettingViewSet(viewsets.GenericViewSet):
    serializer_class = BaseDataSettingSerializer
    def list(self, request):
        results = self.serializer_class({}, many=False).data
        return Response(results)


class SiteSettingViewSet(SingletonViewSet):
    queryset = SiteSetting.objects.all()
    model_class = SiteSetting
    serializer_class = SiteSettingSerializer
    parser_classes = [CamelCaseMultiPartParser, CamelCaseJSONParser]
    permission_classes = [HasAdminAccessOrReadOnlyAny]
    authentication_classes = []


class MatrixStatisticsViewSet(viewsets.GenericViewSet):
    serializer_class = MatrixStatisticsSerializer
    def list(self, request):
        results = self.serializer_class({}, many=False).data
        return Response(results)


