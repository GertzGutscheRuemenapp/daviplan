from django.core.exceptions import BadRequest
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from datentool_backend.user.models import Service
from datentool_backend.indicators.compute import (
    AreaAssessmentIndicator,
    ComputePopulationAreaIndicator,
    NumberOfLocations,
    TotalCapacityInArea,
    DemandAreaIndicator,
    ComputePopulationDetailAreaIndicator)

from datentool_backend.indicators.serializers import (
    PopulationIndicatorSerializer, IndicatorAreaResultSerializer)

from .parameters import (area_level_param,
                         areas_param,
                         year_param,
                         prognosis_param,
                         genders_param,
                         age_groups_param,
                         services_param,
                         scenario_param,
                         )


class FixedIndicatorViewSet(viewsets.GenericViewSet):

    @extend_schema(
        parameters=[area_level_param,
                    areas_param,
                    year_param,
                    prognosis_param,
                    genders_param,
                    age_groups_param,
                    ],
        responses=IndicatorAreaResultSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def aggregate_population(self, request, **kwargs):
        """get the total population for selected areas"""
        qs = ComputePopulationAreaIndicator(self.request.query_params).compute()
        serializer = IndicatorAreaResultSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[area_level_param,
                    year_param,
                    services_param,
                    scenario_param,
                    ],
        responses=IndicatorAreaResultSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def number_of_locations(self, request, **kwargs):
        """get the number of locations with a certain service for selected areas"""
        qs = NumberOfLocations(self.request.query_params).compute()
        serializer = IndicatorAreaResultSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[area_level_param,
                    year_param,
                    services_param,
                    scenario_param,
                    ],
        responses=IndicatorAreaResultSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def capacity(self, request, **kwargs):
        """get the total capacity of a certain service for selected areas"""
        qs = TotalCapacityInArea(self.request.query_params).compute()
        serializer = IndicatorAreaResultSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[area_level_param,
                    areas_param,
                    year_param,
                    scenario_param,
                    services_param,
                    genders_param,
                    age_groups_param,
                    ],
        responses=IndicatorAreaResultSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def demand(self, request, **kwargs):
        """get the total population for selected areas"""
        qs = DemandAreaIndicator(self.request.query_params).compute()
        serializer = IndicatorAreaResultSerializer(qs, many=True)
        return Response(serializer.data)


    @extend_schema(
        parameters=[areas_param,
                    year_param,
                    prognosis_param,
                    genders_param,
                    age_groups_param,
                    ],
        responses=PopulationIndicatorSerializer(many=True),
    )
    @action(methods=['GET'], detail=False)
    def population_details(self, request, **kwargs):
        """get the population details by year, gender and agegroup for the selected areas"""
        qs = ComputePopulationDetailAreaIndicator(self.request.query_params).compute()
        serializer = PopulationIndicatorSerializer(qs, many=True)
        return Response(serializer.data)

