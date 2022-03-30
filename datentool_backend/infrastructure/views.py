from django.db.models import Prefetch, Q
from django.http.request import QueryDict

from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter,
                                   extend_schema_view,
                                   inline_serializer,
                                   )

from datentool_backend.utils.views import ProtectCascadeMixin, ExcelTemplateMixin
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 CanEditBasedata,)

from datentool_backend.infrastructure.permissions import CanEditScenarioPermission

from datentool_backend.user.models import InfrastructureAccess

from datentool_backend.infrastructure.models import (Scenario,
                                                     Place,
                                                     Capacity,
                                                     PlaceField,
                                                     PlaceAttribute,
                                                     )

from datentool_backend.infrastructure.serializers import (ScenarioSerializer,
                                                          PlaceSerializer,
                                                          CapacitySerializer,
                                                          PlaceFieldSerializer,
                                                          PlacesTemplateSerializer,
                                                          infrastructure_id_serializer,
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
        infrastructure_id = request.data.get('infrastructure_id')
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
        infrastructure_id = request.data.get('infrastructure_id')
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
        year = query_params.get('year', 0)
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

