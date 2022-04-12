from django.db.models import Q, Max, ExpressionWrapper, BooleanField
from django.core.exceptions import BadRequest
from django.contrib.auth.models import User
from django_filters import rest_framework as filters

from rest_framework import viewsets, permissions, status, response, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter,
                                   inline_serializer)

from datentool_backend.indicators.compute.base import (
    ServiceIndicator, ResultSerializer)
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import(CanEditBasedata,
                                                HasAdminAccessOrReadOnly,
                                                IsOwner
                                                )
from datentool_backend.indicators.serializers import IndicatorSerializer
from .permissions import CanUpdateProcessPermission, CanPatchSymbol
from .serializers import (UserSerializer,
                          YearSerializer,
                          PlanningProcessSerializer,
                          InfrastructureSerializer,
                          ServiceSerializer,
                          )
from datentool_backend.models import (Year,
                                      PlanningProcess,
                                      Infrastructure,
                                      Service)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [HasAdminAccessOrReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()

    @action(methods=['GET', 'POST', 'PATCH', 'DELETE'], detail=True,
            permission_classes=[IsOwner])
    def usersettings(self, request, **kwargs):
        '''
        retrieve or set settings stored as json at profile object
        can be filtered by passing 'keys' query parameter
        '''
        profile = self.get_object().profile
        data = {}
        if request.data:
            # query dicts wrap all values in lists
            # workaround: assume that single values in lists were originally
            # not send as lists
            data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v
                    for k, v in dict(request.data).items()}

        if request.method == 'POST':
            profile.settings = data
        if request.method == 'PATCH':
            profile.settings.update(data)
        if request.method == 'DELETE':
            profile.settings = {}
        if request.method != 'GET':
            profile.save()

        if 'keys' in request.query_params:
            keys = request.query_params.get('keys').split(',')
            settings = { k: profile.settings[k] for k in keys }
        else:
            settings = profile.settings

        return Response(settings)


class YearFilter(filters.FilterSet):
    active = filters.BooleanFilter(field_name='is_active')
    prognosis = filters.NumberFilter(field_name='population__prognosis')
    has_real_data = filters.BooleanFilter(field_name='has_real')
    has_prognosis_data = filters.BooleanFilter(field_name='has_prognosis')
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
        qs = qs.annotate(
            has_real=ExpressionWrapper(has_real_data,
                                       output_field=BooleanField()),
            has_prognosis=ExpressionWrapper(has_prognosis_data,
                                            output_field=BooleanField()))
        return qs.distinct().order_by('year')

    @extend_schema(description='Set Year Range',
                   request=inline_serializer(
                       name='YearRangeSerializer',
                       fields={
                           'from_year': serializers.IntegerField(required=True),
                           'to_year': serializers.IntegerField(required=True),
                       }
                   )
                )
    @action(methods=['POST'], detail=False)
    def set_range(self, request):
        """create or delete years, if required"""
        try:
            from_year = int(request.data.get('from_year'))
            to_year = int(request.data.get('to_year'))
        except (ValueError, TypeError):
            raise BadRequest('from_year and to_year must be integers')

        years_to_delete = Year.objects.exclude(year__range=(from_year, to_year))
        years_to_delete.delete()

        for y in range(from_year, to_year+1):
            year = Year.objects.get_or_create(year=y)

        qs = Year.objects.all()
        data = self.serializer_class(qs, many=True).data

        return response.Response(data, status=status.HTTP_201_CREATED)


class PlanningProcessViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PlanningProcess.objects.all()
    serializer_class = PlanningProcessSerializer
    permission_classes = [permissions.IsAuthenticated &
                          CanUpdateProcessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        condition_user_in_user = Q(users__in=[self.request.user.profile])
        condition_owner_in_user = Q(owner=self.request.user.profile)
        return qs.filter(condition_user_in_user |
                         condition_owner_in_user).distinct()


class InfrastructureViewSet(ProtectCascadeMixin,
                            viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
    permission_classes = [CanPatchSymbol]


class ServiceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Service.objects.all().annotate(
        max_capacity=Max('capacity__capacity'))
    serializer_class = ServiceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    @extend_schema(
        description='Indicators available for this service',
        responses=IndicatorSerializer(many=True),
    )
    @action(methods=['GET'], detail=True)
    def get_indicators(self, request, **kwargs):
        service_id = kwargs.get('pk')
        service: Service = Service.objects.get(id=service_id)
        indicators = []
        for indicator_class in ServiceIndicator.registered.values():
            if indicator_class.capacity_required and not service.has_capacity:
                continue
            indicators.append(indicator_class(service))
        serializer = IndicatorSerializer(indicators, many=True)
        return Response(serializer.data)

    @extend_schema(
        description=('Compute indicator for this service, structure of result '
                     'depends on "result_type" of indicator'),
        responses=dict((f'result_type: {k.lower()}', v.value(many=True))
                       for k, v in ResultSerializer._member_map_.items()),
        parameters=[
            OpenApiParameter(
                name='indicator', required=True, type=str,
                description=('name of indicator to compute with'))
        ]
    )
    @action(methods=['POST'], detail=True)
    def compute_indicator(self, request, **kwargs):
        indicator_name = request.data.get('indicator')
        if not indicator_name:
            raise BadRequest('query parameter "indicator" is required')
        indicator_class = ServiceIndicator.registered.get(indicator_name)
        if not indicator_class:
            raise BadRequest(f'indicator "{indicator_name}" unknown')
        service_id = kwargs.get('pk')
        service: Service = Service.objects.get(id=service_id)
        indicator = indicator_class(service, request.query_params)
        results = indicator.compute()

        return Response(indicator.serialize(results))

