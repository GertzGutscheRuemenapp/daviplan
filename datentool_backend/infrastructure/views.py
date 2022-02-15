import json

from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata,)

from .permissions import CanEditScenarioPermission

from datentool_backend.user.models import InfrastructureAccess

from .models import (Scenario,
                     Place,
                     Capacity,
                     PlaceField,
                     )

from .serializers import (ScenarioSerializer,
                          PlaceSerializer,
                          CapacitySerializer,
                          PlaceFieldSerializer,
                          )


class ScenarioViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    permission_classes = [CanEditScenarioPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        condition_user_in_user = Q(planning_process__users__in=[self.request.user.profile])
        condition_owner_in_user = Q(planning_process__owner=self.request.user.profile)

        return qs.filter(condition_user_in_user | condition_owner_in_user)


capacity_params = [
    OpenApiParameter(name='service', type={'type': 'array', 'items': {'type': 'integer'}},
                     description='pkeys of the services', required=False),
    OpenApiParameter(name='year', type=int,
                     description='get capacities for this year', required=False),
    OpenApiParameter(name='scenario', type=int, required=False,
                     description='get capacities for the scenario with this pkey'),
]


@extend_schema_view(list=extend_schema(description='List Places',
                                       parameters=capacity_params),
                    retrieve=extend_schema(description='Get Place with id',
                                           parameters=capacity_params),)
class PlaceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):

    serializer_class = PlaceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


    def get_queryset(self):
        profile = self.request.user.profile
        accessible = InfrastructureAccess.objects.filter(
            profile=profile).values_list('infrastructure', flat=True)
        queryset = Place.objects.filter(infrastructure__in=accessible)
        service = self.request.query_params.get('service')
        if service:
            queryset = queryset.filter(service_capacity=service).distinct()
        return queryset


@extend_schema_view(list=extend_schema(description='List capacities',
                                       parameters=capacity_params),
                    retrieve=extend_schema(description='Get capacities for id',
                                           parameters=capacity_params),
                                        )
class CapacityViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PlaceFieldViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PlaceField.objects.all()
    serializer_class = PlaceFieldSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

