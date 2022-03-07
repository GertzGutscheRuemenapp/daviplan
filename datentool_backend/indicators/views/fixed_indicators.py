from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

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

from .parameters import (area_level_param,
                         areas_param,
                         year_param,
                         prognosis_param,
                         genders_param,
                         age_groups_param,
                         services_param,
                         scenario_param,
                         place_param, loc_x_param, loc_y_param
                         )


class FixedIndicatorViewSet(viewsets.GenericViewSet):
    serializer_class = IndicatorSerializer

    @extend_schema(
        description='Indicator description',
        responses=IndicatorSerializer(many=False),
        methods=['GET']
    )
    @extend_schema(
        description='get the total population for selected areas',
        parameters=[area_level_param,
                    areas_param,
                    year_param,
                    prognosis_param,
                    genders_param,
                    age_groups_param,
                    ],
        request=IndicatorSerializer(many=False),
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
        parameters=[area_level_param,
                    year_param,
                    services_param,
                    scenario_param,
                    ],
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
        parameters=[area_level_param,
                    year_param,
                    services_param,
                    scenario_param,
                    ],
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
        parameters=[area_level_param,
                    areas_param,
                    year_param,
                    scenario_param,
                    services_param,
                    genders_param,
                    age_groups_param,
                    ],
        responses=DemandAreaIndicator.result_serializer.value(many=True),
        methods=['POST']
    )
    @action(methods=['GET', 'POST'], detail=False)
    def demand(self, request, **kwargs):
        """get the total population for selected areas"""
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
        parameters=[areas_param,
                    year_param,
                    prognosis_param,
                    genders_param,
                    age_groups_param,
                    ],
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
        parameters=[place_param],
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
        parameters=[loc_x_param, loc_y_param],
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
