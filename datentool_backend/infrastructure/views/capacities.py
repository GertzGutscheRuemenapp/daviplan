from django.db.models import Prefetch, Max, Q, Count, Sum
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter,
                                   extend_schema_view,
                                   inline_serializer,
                                   OpenApiResponse
                                   )
from django.core.exceptions import BadRequest
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (HasAdminAccess,
                                                 HasAdminAccessOrReadOnly,
                                                 CanEditBasedata,
                                                 )

from datentool_backend.models import (
    Place, Capacity, Service, Scenario)

from datentool_backend.infrastructure.permissions import (
    ScenarioCapacitiesPermission,
    HasPermissionForScenario)

from datentool_backend.infrastructure.serializers import CapacitySerializer
from datentool_backend.utils.serializers import MessageSerializer


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

    def get_permissions(self):
        if self.action in ['list']:
            permission_classes = [HasAdminAccess | HasPermissionForScenario]
        else:
            permission_classes = [HasAdminAccessOrReadOnly |
                                  CanEditBasedata |
                                  ScenarioCapacitiesPermission]
        return [permission() for permission in permission_classes]


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
        # iterate instead of bulk delete to trigger model delete()
        for cap in existing.exclude(id__in=keep):
            cap.delete()
        queryset = Capacity.filter_queryset(
            Capacity.objects.filter(place=place),
            service_ids=[service],
            scenario_id=scenario)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
