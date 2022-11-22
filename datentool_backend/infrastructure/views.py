from django.db.models import Prefetch, Max, Q, Count, Sum
from django.http.request import QueryDict
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter,
                                   extend_schema_view,
                                   inline_serializer,
                                   OpenApiResponse
                                   )
from django.core.exceptions import BadRequest
from djangorestframework_camel_case.util import camelize

from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from datentool_backend.utils.views import ProtectCascadeMixin, ExcelTemplateMixin
from datentool_backend.utils.permissions import (HasAdminAccess,
                                                 HasAdminAccessOrReadOnly,
                                                 CanEditBasedata)
from datentool_backend.models import (
    InfrastructureAccess, Infrastructure, Place, Capacity, PlaceField,
    PlaceAttribute, Service, Scenario)
from .permissions import (CanPatchSymbol, ScenarioCapacitiesPermission,
                          CanEditScenarioPlacePermission)
from datentool_backend.infrastructure.serializers import (
    PlaceSerializer,
    CapacitySerializer,
    PlaceFieldSerializer,
    PlacesTemplateSerializer,
    infrastructure_id_serializer,
    ServiceSerializer,
    InfrastructureSerializer,
    ServiceCapacityByScenarioSerializer)
from datentool_backend.indicators.compute.base import (
    ServiceIndicator,
    ResultSerializer)
from datentool_backend.indicators.serializers import IndicatorSerializer
from datentool_backend.utils.serializers import MessageSerializer


@extend_schema_view(list=extend_schema(description='List Places',
                                       parameters=[]),
                    retrieve=extend_schema(description='Get Place with id'))
class PlaceViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):

    serializer_class = PlaceSerializer
    serializer_action_classes = {
        'create_template': PlacesTemplateSerializer,
        'upload_template': PlacesTemplateSerializer}
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata |
                          CanEditScenarioPlacePermission]
    filterset_fields = ['infrastructure']

    def create(self, request, *args, **kwargs):
        """use the annotated version"""
        attributes = request.data.get('attributes')
        request.data['attributes'] = camelize(attributes)
        serializer = self.get_serializer(data=request.data)
        # ToDo: return error response
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        #replace the created instance with an annotated instance
        serializer.instance = Place.objects.get(pk=serializer.instance.pk)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        attributes = request.data.get('attributes')
        request.data['attributes'] = camelize(attributes)
        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        try:
            profile = self.request.user.profile
        except AttributeError:
            # no profile yet
            return Place.objects.none()
        accessible_infrastructure = InfrastructureAccess.objects.filter(profile=profile)

        queryset = Place.objects.select_related('infrastructure')\
            .prefetch_related(
                Prefetch('infrastructure__infrastructureaccess_set',
                         queryset=accessible_infrastructure,
                         to_attr='users_infra_access'),
                Prefetch('placeattribute_set',
                         queryset=PlaceAttribute.objects.select_related('field__field_type'))
                )

        return queryset

    # only filtering for list view
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        scenario = self.request.query_params.get('scenario')
        if scenario is not None:
            queryset = queryset.filter(Q(scenario=scenario) | Q(scenario__isnull=True))
        else:
            queryset = queryset.filter(scenario__isnull=True)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(description='Create Excel-Template to download',
                   request=inline_serializer(
                       name='PlaceCreateSerializer',
                       fields={'infrastructure': infrastructure_id_serializer}
                   ),
                   )
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccess | CanEditBasedata])
    def create_template(self, request):
        """Download the Template"""
        infrastructure_id = request.data.get('infrastructure')
        return super().create_template(request, infrastructure_id=infrastructure_id)

    @extend_schema(description='Upload Excel-File with Places and Capacities',
                   request=inline_serializer(
                       name='PlaceFileUploadSerializer',
                       fields={'excel_file': serializers.FileField(),}
                   ))
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccess | CanEditBasedata],
            parser_classes=[CamelCaseMultiPartParser])
    def upload_template(self, request):
        """Download the Template"""
        # no constraint dropping, because we use individual updates
        data = QueryDict(mutable=True)
        data.update(self.request.data)
        data['drop_constraints'] = 'False'
        request._full_data = data

        queryset = Place.objects.none()
        return super().upload_template(request,
                                       queryset=queryset,)

    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def clear(self, request, **kwargs):
        infrastructure_id = request.data.get('infrastructure')
        if (infrastructure_id is not None):
            places = Place.objects.filter(infrastructure=infrastructure_id)
        else:
            places = Place.objects.all()
        count = places.count()
        places.delete()
        return Response({'message': f'{count} Areas deleted'},
                        status=status.HTTP_200_OK)


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
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata |
                          ScenarioCapacitiesPermission]

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


    @extend_schema(description=('replace all occurences of capacities for '
                                'service/place/scenario-combination'),
                   request=inline_serializer(
                       name='ReplaceCapacitiesSerializer',
                       fields={'scenario': serializers.IntegerField(),
                               'service': serializers.IntegerField(),
                               'place': serializers.IntegerField(),
                               'capacities': CapacitySerializer(
                                   many=True, required=False),
                               }
                   ),
                   responses={202: CapacitySerializer(many=True),
                              400: OpenApiResponse(MessageSerializer,
                                                   'Bad Request')})
    @action(methods=['POST'], detail=False)
    def replace(self, request, **kwargs):
        scenario = request.data.get('scenario')
        service = request.data.get('service')
        place = request.data.get('place')
        capacities = request.data.get('capacities', [])
        if scenario is None or service is None or place is None:
            raise BadRequest('service, place and scenario required')
        service = Service.objects.get(id=service)
        scenario = Scenario.objects.get(id=scenario)
        place = Place.objects.get(id=place)
        # ToDo: check permission to edit scenario

        existing = Capacity.objects.filter(
            scenario=scenario, service=service, place=place)
        keep = []
        for capacity in capacities:
            # look if there is already a capacity for this year defined in
            # scenario
            try:
                # keep and update it
                ex_cap = existing.get(from_year=capacity['from_year'])
                ex_cap.capacity = capacity['capacity']
                ex_cap.save()
                keep.append(ex_cap.id)
            except Capacity.DoesNotExist:
                # create new one
                cap = Capacity.objects.create(
                    service=service, scenario=scenario, place=place,
                    capacity=capacity['capacity'],
                    from_year=capacity['from_year'])
                keep.append(cap.id)
        existing.exclude(id__in=keep).delete()
        queryset = Capacity.filter_queryset(
            Capacity.objects.filter(place=place),
            service_ids=[service],
            scenario_id=scenario)
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

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Infrastructure.objects.all()
        try:
            profile = self.request.user.profile
        except AttributeError:
            # no profile yet
            return Infrastructure.objects.none()
        if profile.admin_access:
            return Infrastructure.objects.all()

        accessible = InfrastructureAccess.objects.filter(
            profile=profile).values_list('infrastructure__id')
        return Infrastructure.objects.filter(id__in=accessible)


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

    @extend_schema(
        description='Number of Places and Total capacity in scenarios',
        request=inline_serializer(
            name='ScenariosYearSerializer',
            fields={'year': serializers.IntegerField(required=False,
                                         help_text='Jahr (z.B. 2010)'),
                    'scenario_ids': serializers.ListField(
                        child=serializers.IntegerField(),
                        required=True, help_text='scenario ids'),
                    }
        ),
        responses=ServiceCapacityByScenarioSerializer(many=True),
    )
    @action(methods=['GET'], detail=True)
    def total_capacity_in_year(self, request, **kwargs):
        service_id = kwargs.get('pk')
        year = self.request.query_params.get('year')
        scenario_ids = self.request.query_params.getlist('scenario_ids')
        data = []

        for scenario_id in scenario_ids:
            scenario_id = scenario_id or None

            capacity = Capacity.objects.all()
            capacity2 = Capacity.filter_queryset(capacity,
                                                service_ids=[service_id],
                                                scenario_id=scenario_id,
                                                year=year)
            capacity3 = capacity2\
                .filter(capacity__gt=0)\
                .aggregate(
                n_places=Count('id'),
                total_capacity=Sum('capacity'))
            capacity3['scenario_id'] = int(scenario_id)
            data.append(capacity3)

        serializer = ServiceCapacityByScenarioSerializer(data, many=True)
        return Response(serializer.data)