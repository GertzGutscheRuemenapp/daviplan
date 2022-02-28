from rest_framework import viewsets
from distutils.util import strtobool
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)


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
