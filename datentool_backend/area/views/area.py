from django.core.exceptions import BadRequest
from django.http import Http404
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, OpenApiParameter

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 CanEditBasedata)

from datentool_backend.area.models import Area, FieldType, AreaField

from datentool_backend.area.serializers import (AreaSerializer,
                                                FieldTypeSerializer,
                                                AreaFieldSerializer,
                                                )
from datentool_backend.area.permissions import ProtectPresetPermission


class AreaViewSet(ProtectCascadeMixin,
                  viewsets.ModelViewSet):

    serializer_class = AreaSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        """return the annotated queryset"""
        if self.detail:
            try:
                area_level = Area.objects.get(**self.kwargs).area_level_id
            except Area.DoesNotExist as e:
                raise Http404(str(e))
        else:
            area_level = self.request.query_params.get('area_level')
        if not area_level:
            raise BadRequest('No AreaLevel provided')
        areas = Area.label_annotated_qs(area_level)
        return areas

    @extend_schema(
        parameters=[OpenApiParameter(name='area_level', required=True, type=int)]
    )
    def list(self, request):
        return super().list(request)


class FieldTypeViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = FieldType.objects.all()
    serializer_class = FieldTypeSerializer
    permission_classes = [ProtectPresetPermission &
                          (HasAdminAccessOrReadOnly | CanEditBasedata)]

    def update(self, request, *args, **kwargs):
        """put the ftype_id into the classifications"""
        ftype = FieldType(pk=kwargs['pk'])
        for classification in request.data.get('classification', []):
            classification['ftype_id'] = ftype.pk
        return super().update(request, *args, **kwargs)


class AreaFieldViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = AreaField.objects.all()
    serializer_class = AreaFieldSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

