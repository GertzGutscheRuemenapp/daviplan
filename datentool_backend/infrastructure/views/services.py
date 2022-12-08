from django.db.models import Max, Count, Sum
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter,
                                   inline_serializer,
                                   )
from django.core.exceptions import BadRequest

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (HasAdminAccess,
                                                 HasAdminAccessOrReadOnly,
                                                 CanEditBasedata,
                                                 )

from datentool_backend.models import (Capacity, Service, Scenario)

from datentool_backend.infrastructure.permissions import HasPermissionForScenario

from datentool_backend.infrastructure.serializers import (
    ServiceSerializer,
    ServiceCapacityByScenarioSerializer)

from datentool_backend.indicators.compute.base import (
    ServiceIndicator,
    ResultSerializer)

from datentool_backend.indicators.serializers import IndicatorSerializer


class ServiceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Service.objects.all().annotate(
        max_capacity=Max('capacity__capacity'))
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ['compute_indicator', 'total_capacity_in_year']:
            permission_classes = [HasAdminAccess | HasPermissionForScenario]
        else:
            permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
        return [permission() for permission in permission_classes]


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
                    'planningprocess': serializers.IntegerField(
                        help_text='planning process id'),
                    'scenario': serializers.IntegerField(
                        help_text='scenario id'),
                    }
        ),
        responses=ServiceCapacityByScenarioSerializer(many=True),
    )
    @action(methods=['GET'], detail=True)
    def total_capacity_in_year(self, request, **kwargs):
        service_id = kwargs.get('pk')
        year = self.request.query_params.get('year')
        planning_process_id = self.request.query_params.get('planningprocess')
        scenario_id = self.request.query_params.get('scenario')
        data = []
        if scenario_id:
            scenario_ids = [scenario_id]
        else:
            scenarios = Scenario.objects.all()
            if planning_process_id:
                scenarios = scenarios.filter(planning_process=planning_process_id)
            scenario_ids = [None] + list(scenarios.values_list('id', flat=True))

        for scenario_id in scenario_ids:
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
            scenario_id = scenario_id if scenario_id else 0
            capacity3['scenario_id'] = int(scenario_id)
            data.append(capacity3)

        serializer = ServiceCapacityByScenarioSerializer(data, many=True)
        return Response(serializer.data)
