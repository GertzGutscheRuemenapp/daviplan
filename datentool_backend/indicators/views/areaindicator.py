from django.http.request import QueryDict
from django.views.generic import DetailView
from django.core.exceptions import BadRequest
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from vectortiles.postgis.views import MVTView, BaseVectorTileView
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from datentool_backend.area.models import AreaLevel
from datentool_backend.indicators.models import (Indicator,
                     IndicatorType,
                     )
from datentool_backend.indicators.compute import (
    ComputeIndicator,
    ComputePopulationAreaIndicator,
    NumberOfLocations,
    TotalCapacityInArea,
    )
from datentool_backend.indicators.serializers import (IndicatorTypeSerializer,
                          IndicatorSerializer,
                          AreaIndicatorSerializer,
                          )
from .parameters import (area_level_param,
                         areas_param,
                         year_param,
                         prognosis_param,
                         genders_param,
                         age_groups_param,
                         services_param,
                         scenario_param,
                         )


@extend_schema_view(list=extend_schema(
    description='Get indicator calculated for the areas',
    parameters=[
        OpenApiParameter(name='indicator', type=int,
                         description='pk of the indicator to calculate'),
    ]))
class AreaIndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Indicator.objects.none()
    serializer_class = AreaIndicatorSerializer

    def get_queryset(self):
        indicator_id = self.request.query_params.get('indicator')
        if indicator_id is None:
            raise BadRequest('indicator_id is required as query_param')

        try:
            classname = Indicator.objects.get(pk=indicator_id).indicator_type.classname
        except Indicator.DoesNotExist:
            raise BadRequest(f'indicator with id {indicator_id} not found')
        compute_class: ComputeIndicator = IndicatorType._indicator_classes[classname]
        qs = compute_class(self.request.query_params).compute()
        return qs

    @extend_schema(
        parameters=[area_level_param,
                    areas_param,
                    year_param,
                    prognosis_param,
                    genders_param,
                    age_groups_param,
                    ],
        responses=AreaIndicatorSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def aggregate_population(self, request, **kwargs):
        """get the total population for selected areas"""
        qs = ComputePopulationAreaIndicator(self.request.query_params).compute()
        serializer = AreaIndicatorSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[area_level_param,
                    year_param,
                    services_param,
                    scenario_param,
                    ],
        responses=AreaIndicatorSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def number_of_locations(self, request, **kwargs):
        """get the number of locations with a certain service for selected areas"""
        qs = NumberOfLocations(self.request.query_params).compute()
        serializer = AreaIndicatorSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[area_level_param,
                    year_param,
                    services_param,
                    scenario_param,
                    ],
        responses=AreaIndicatorSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def capacity(self, request, **kwargs):
        """get the total capacity of a certain service for selected areas"""
        qs = TotalCapacityInArea(self.request.query_params).compute()
        serializer = AreaIndicatorSerializer(qs, many=True)
        return Response(serializer.data)


class AreaLevelIndicatorTileView(MVTView, DetailView):
    model = AreaLevel
    vector_tile_fields = ('id', 'area_level', 'label', 'value')

    def get_vector_tile_layer_name(self) -> str:
        """The name of the area-level"""
        return self.get_object().name

    def get_vector_tile_queryset(self):
        """Calculate the indicators for each area of the area-level"""
        query_params = QueryDict(mutable=True)
        query_params.update(self.request.GET)
        # set the area_level as query_param
        query_params['area_level'] = self.object.pk

        # an indicator_id is required
        indicator_id = query_params.get('indicator')
        if indicator_id is None:
            raise BadRequest('indicator_id is required as query_param')

        # get the IndicatorCompute-class
        try:
            classname = Indicator.objects.get(pk=indicator_id).indicator_type.classname
        except Indicator.DoesNotExist:
            raise BadRequest(f'indicator with id {indicator_id} not found')
        compute_class: ComputeIndicator = IndicatorType._indicator_classes[classname]
        # and compute the queryset for the areas
        areas = compute_class(query_params).compute()
        return areas

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return BaseVectorTileView.get(self, request=request, z=kwargs.get('z'),
                                      x=kwargs.get('x'), y=kwargs.get('y'))

