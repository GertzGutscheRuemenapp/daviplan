from django.db.models import Prefetch, Max
from django.http.request import QueryDict
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter,
                                   extend_schema_view,
                                   inline_serializer,
                                   )
from django.core.exceptions import BadRequest

from datentool_backend.utils.views import ProtectCascadeMixin, ExcelTemplateMixin
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 CanEditBasedata,)
from datentool_backend.models import (
    InfrastructureAccess, Infrastructure, Place, Capacity, PlaceField,
    PlaceAttribute, Service)
from .permissions import CanPatchSymbol
from datentool_backend.infrastructure.serializers import (
    PlaceSerializer, CapacitySerializer, PlaceFieldSerializer,
    PlacesTemplateSerializer, infrastructure_id_serializer,
    ServiceSerializer, InfrastructureSerializer)
from datentool_backend.indicators.compute.base import (
    ServiceIndicator, ResultSerializer)
from datentool_backend.indicators.serializers import IndicatorSerializer


@extend_schema_view(list=extend_schema(description='List Places',
                                       parameters=[]),
                    retrieve=extend_schema(description='Get Place with id'))
class PlaceViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):

    serializer_class = PlaceSerializer
    serializer_action_classes = {
        'create_template': PlacesTemplateSerializer,
        'upload_template': PlacesTemplateSerializer}
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_fields = ['infrastructure']

    def create(self, request, *args, **kwargs):
        """use the annotated version"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        #replace the created instance with an annotated instance
        serializer.instance = self.get_queryset().get(pk=serializer.instance.pk)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        try:
            profile = self.request.user.profile
        except AttributeError:
            # no profile yet
            return Place.objects.none()
        accessible_infrastructure = InfrastructureAccess.objects.filter(profile=profile)

        scenario = self.request.query_params.get('scenario')
        queryset = Place.objects.all()
        if scenario is not None:
            queryset = queryset.filter(scenario=scenario)
        else:
            queryset = queryset.filter(scenario__isnull=True)

        queryset = Place.objects.select_related('infrastructure')\
            .prefetch_related(
                Prefetch('infrastructure__infrastructureaccess_set',
                         queryset=accessible_infrastructure,
                         to_attr='users_infra_access'),
                Prefetch('placeattribute_set',
                         queryset=PlaceAttribute.objects.select_related('field__field_type'))
                )
        return queryset

    @extend_schema(description='Create Excel-Template to download',
                   request=inline_serializer(
                       name='PlaceCreateSerializer',
                       fields={'infrastructure_id': infrastructure_id_serializer}
                       ),
                   )
    @action(methods=['POST'], detail=False, permission_classes=[CanEditBasedata])
    def create_template(self, request):
        """Download the Template"""
        infrastructure_id = request.data.get('infrastructure')
        return super().create_template(request, infrastructure_id=infrastructure_id)

    @extend_schema(description='Upload Excel-File with Places and Capacities',
                   request=inline_serializer(
                       name='PlaceFileDropConstraintSerializer',
                       fields={'infrastructure_id': infrastructure_id_serializer,
                               #'drop_constraints': drop_constraints,
                               'excel_file': serializers.FileField(),
                               }
                       )
                   )
    @action(methods=['POST'], detail=False, permission_classes=[CanEditBasedata])
    def upload_template(self, request):
        """Download the Template"""
        infrastructure_id = request.data.get('infrastructure')
        # no constraint dropping, because we use individual updates
        data = QueryDict(mutable=True)
        data.update(self.request.data)
        data['drop_constraints'] = 'False'
        request._full_data = data

        queryset = Place.objects.none()
        return super().upload_template(request,
                                       queryset=queryset,
                                       infrastructure_id=infrastructure_id)


capacity_params = [
    OpenApiParameter(name='service',
                     type={'type': 'array', 'items': {'type': 'integer'}},
                     description='pkeys of the services', required=False),
    OpenApiParameter(name='place',
                     type={'type': 'array', 'items': {'type': 'integer'}},
                     description='pkeys of the places', required=False),
    OpenApiParameter(name='year', type=int,
                     description='get capacities for this year', required=False),
    OpenApiParameter(name='scenario', type=int, required=False,
                     description='get capacities for the scenario with this pkey'),
]
@extend_schema_view(list=extend_schema(description='List Capacities',
                                       parameters=capacity_params),
                    retrieve=extend_schema(description='Get Capacity with id',
                                           parameters=capacity_params),)
class CapacityViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    # only filtering for list view
    def list(self, request, *args, **kwargs):
        query_params = self.request.query_params
        service_ids = query_params.getlist('service')
        year = query_params.get('year')
        scenario = query_params.get('scenario')
        places = query_params.getlist('place')

        queryset = self.queryset
        if places:
            queryset = self.queryset.filter(place__in=places)

        queryset = Capacity.filter_queryset(queryset,
                                            service_ids=service_ids,
                                            scenario_id=scenario,
                                            year=year)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PlaceFieldViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PlaceField.objects.all()
    serializer_class = PlaceFieldSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


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
        data = request.data
        data['service'] = service_id
        indicator = indicator_class(service, data)
        results = indicator.compute()

        return Response(indicator.serialize(results))

