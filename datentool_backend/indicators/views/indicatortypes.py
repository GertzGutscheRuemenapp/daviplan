from rest_framework import viewsets
from distutils.util import strtobool
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from datentool_backend.area.models import AreaLevel
from datentool_backend.indicators.models import (Indicator,
                     IndicatorType,
                     )
from datentool_backend.indicators.compute import (ComputeIndicator,
                      ComputePopulationAreaIndicator,
                      ComputePopulationDetailAreaIndicator,
                      )
from datentool_backend.indicators.serializers import (IndicatorTypeSerializer,
                          IndicatorSerializer,
                          )


@extend_schema_view(list=extend_schema(
    description='List available IndicatorTypes',
    parameters=[
        OpenApiParameter(name='classname',
                         description='names of the IndicatorType-Classes',
                         type={'type': 'array', 'items': {'type': 'str'}},),
        OpenApiParameter(name='category', type=str),
        OpenApiParameter(name='userdefined', type=bool),
    ]))
class IndicatorTypeViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = IndicatorType.objects.all()
    serializer_class = IndicatorTypeSerializer

    def get_queryset(self):
        IndicatorType._update_indicators_types()
        qs = super().get_queryset()
        params = {}
        classnames = self.request.query_params.getlist('classname')
        if classnames:
            params['classname__in'] = classnames
        categories = self.request.query_params.getlist('category')
        if categories:
            params['category__in'] = categories
        userdefined = self.request.query_params.get('userdefined')
        if userdefined:
            params['userdefined'] = bool(strtobool(userdefined))
        qs = qs.filter(**params)
        return qs


@extend_schema_view(list=extend_schema(
    description='List available Indicators',
    parameters=[
        OpenApiParameter(name='indicatortype_classname',
                         description='names of the IndicatorType-Classes',
                         type={'type': 'array', 'items': {'type': 'str'}},),
        OpenApiParameter(name='name',
                         description='names of the Indicators',
                         type={'type': 'array', 'items': {'type': 'str'}},),
        OpenApiParameter(name='userdefined', type=bool),
    ]))
class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        qs = super().get_queryset()
        params = {}
        classnames = self.request.query_params.getlist('indicatortype_classname')
        if classnames:
            params['indicator_type__classname__in'] = classnames
        names = self.request.query_params.getlist('name')
        if names:
            params['name__in'] = names
        userdefined = self.request.query_params.getlist('userdefined')
        if userdefined:
            params['userdefined'] = userdefined
        qs = qs.filter(**params)
        return qs
