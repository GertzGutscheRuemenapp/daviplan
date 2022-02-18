from django.core.exceptions import BadRequest
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter


from datentool_backend.indicators.models import Indicator, IndicatorType

from datentool_backend.indicators.compute import (ComputeIndicator,
                                                  ComputePopulationDetailAreaIndicator)

from datentool_backend.indicators.serializers import PopulationIndicatorSerializer

from .parameters import (areas_param,
                         year_param,
                         prognosis_param,
                         genders_param,
                         age_groups_param,)


@extend_schema_view(list=extend_schema(
    description='Get indicator calculated for the population',
    parameters=[
        OpenApiParameter(name='indicator', type=int,
                         description='pk of the indicator to calculate'),
    ]))
class PopulationIndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Indicator.objects.none()
    serializer_class = PopulationIndicatorSerializer

    def get_queryset(self):
        #  filter the capacity returned for the specific service
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
