from django.db import models
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer

from datentool_backend.indicators.compute import (
    ComputePopulationAreaIndicator,
    NumberOfLocations,
    TotalCapacityInArea,
    DemandAreaIndicator,
    ComputePopulationDetailIndicator,
    ReachabilityPlace,
    ReachabilityCell
)

from datentool_backend.indicators.serializers import (IndicatorSerializer)

from .parameters import (arealevel_year_service_scenario_serializer,
                         area_agegroup_gender_prognosis_year_fields,
                         arealevel_area_agegroup_gender_prognosis_year_fields)


class FixedIndicatorViewSet(viewsets.GenericViewSet):
    serializer_class = IndicatorSerializer
    queryset = models.QuerySet() # dummy queryset

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        description='get the total population for selected areas',
        request=inline_serializer(
            name='InlinePopulationAreaSerializer',
            fields=arealevel_area_agegroup_gender_prognosis_year_fields,
        ),
        responses=ComputePopulationAreaIndicator.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def aggregate_population(self, request, **kwargs):
        indicator = ComputePopulationAreaIndicator(self.request.data)
        if request.method == 'GET':
            return Response(IndicatorSerializer(indicator).data)
        qs = indicator.compute()
        return Response(indicator.serialize(qs))

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        request=arealevel_year_service_scenario_serializer,
        responses=NumberOfLocations.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def number_of_locations(self, request, **kwargs):
        """get the number of locations with a certain service for selected areas"""
        indicator = NumberOfLocations(self.request.data)
        if request.method == 'GET':
            return Response(IndicatorSerializer(indicator).data)
        qs = indicator.compute()
        return Response(indicator.serialize(qs))

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        request=arealevel_year_service_scenario_serializer,
        responses=TotalCapacityInArea.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def capacity(self, request, **kwargs):
        """get the total capacity of a certain service for selected areas"""
        indicator = TotalCapacityInArea(self.request.data)
        if request.method == 'GET':
            return Response(IndicatorSerializer(indicator).data)
        qs = indicator.compute()
        return Response(indicator.serialize(qs))

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        request=arealevel_year_service_scenario_serializer,
        responses=DemandAreaIndicator.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def demand(self, request, **kwargs):
        """get the total demand for selected services in selected areas"""
        indicator = DemandAreaIndicator(self.request.data)
        if request.method == 'GET':
            return Response(IndicatorSerializer(indicator).data)
        qs = indicator.compute()
        return Response(indicator.serialize(qs))

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        request=inline_serializer(
            name='InlinePopulationDetailSerializer',
            fields=area_agegroup_gender_prognosis_year_fields,
        ),
        responses=ComputePopulationDetailIndicator.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def population_details(self, request, **kwargs):
        """get the population details by year, gender and agegroup for the selected areas"""
        indicator = ComputePopulationDetailIndicator(self.request.data)
        if request.method == 'GET':
            return Response(IndicatorSerializer(indicator).data)
        qs = indicator.compute()
        return Response(indicator.serialize(qs))

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        request=inline_serializer(
            name='PlaceIdSerializer',
            fields={
                'place': serializers.IntegerField(required=True),
                'mode': serializers.CharField(required=True),
            }
        ),
        responses=ReachabilityPlace.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def reachability_place(self, request, **kwargs):
        """get cells with reachabilities to given place"""
        indicator = ReachabilityPlace(self.request.data)
        if request.method == 'GET':
            return Response(IndicatorSerializer(indicator).data)
        qs = indicator.compute()
        return Response(indicator.serialize(qs))

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        request=inline_serializer(
            name='LatLonSerializer',
            fields={
                'lon': serializers.FloatField(required=True, label='x-coord',
                                              help_text='WGS84-Longitude'),
                'lat': serializers.FloatField(required=True, label='y-coord',
                                              help_text='WGS84-Latitude'),
                'mode': serializers.CharField(required=True),
            }
        ),
        responses=ReachabilityCell.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def reachibility_cells(self, request, **kwargs):
        """get places with reachabilities to cells"""
        indicator = ReachabilityCell(self.request.data)
        if request.method == 'GET':
            return Response(IndicatorSerializer(indicator).data)
        qs = indicator.compute()
        return Response(indicator.serialize(qs))
