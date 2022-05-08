from datentool_backend.utils.views import SingletonViewSet
from rest_framework import viewsets
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import ExpressionWrapper, BooleanField, Q, Count
from django.core.exceptions import BadRequest
from drf_spectacular.utils import (extend_schema, inline_serializer,
                                   OpenApiResponse)
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action

from datentool_backend.utils.serializers import MessageSerializer
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 HasAdminAccessOrReadOnlyAny)
from datentool_backend.utils.permissions import CanEditBasedata
from datentool_backend.utils.views import ProtectCascadeMixin
from .models import SiteSetting, ProjectSetting, Year
from .serializers import (SiteSettingSerializer, ProjectSettingSerializer,
                          BaseDataSettingSerializer, YearSerializer)


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
    filter_class = YearFilter

    def get_queryset(self):
        """ get the years. Request-parameters with_prognosis/with_population """
        qs = Year.objects.all()

        has_real_data = (Q(population__isnull=False) &
                         Q(population__prognosis__isnull=True))
        has_prognosis_data = Q(population__prognosis__isnull=False)
        has_statistics_data = Q(stat_count__gt=0)

        qs = qs.annotate(stat_count=Count('statistics')).annotate(
            has_real=ExpressionWrapper(has_real_data,
                                       output_field=BooleanField()),
            has_prognosis=ExpressionWrapper(has_prognosis_data,
                                            output_field=BooleanField()),
            has_statistics=ExpressionWrapper(has_statistics_data,
                                             output_field=BooleanField()),
        )
        return qs.distinct().order_by('year')

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
        if isinstance(years, str):
            years = years.split(',')
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
        if isinstance(years, str):
            years = years.split(',')
        Year.objects.update(is_prognosis=False)
        update_years = Year.objects.filter(year__in=years)
        update_years.update(is_prognosis=True)
        return Response(self.serializer_class(update_years, many=True).data,
                        status=status.HTTP_201_CREATED)


class ProjectSettingViewSet(SingletonViewSet):
    queryset = ProjectSetting.objects.all()
    model_class = ProjectSetting
    serializer_class = ProjectSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnly]


class BaseDataSettingViewSet(viewsets.GenericViewSet):
    serializer_class = BaseDataSettingSerializer
    def list(self, request):
        results = self.serializer_class({}, many=False).data
        return Response(results)


class SiteSettingViewSet(SingletonViewSet):
    queryset = SiteSetting.objects.all()
    model_class = SiteSetting
    serializer_class = SiteSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnlyAny]

