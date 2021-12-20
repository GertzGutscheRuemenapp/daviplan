from rest_framework import viewsets
from datentool_backend.utils.views import ReadOnlyAccess

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)
from .serializers import (CapacityUploadLogSerializer, PlaceUploadLogSerializer,
                          AreaUploadLogSerializer)


class CapacityUploadLogViewSet(ReadOnlyAccess, viewsets.ReadOnlyModelViewSet):
    queryset = CapacityUploadLog.objects.all()
    serializer_class = CapacityUploadLogSerializer


class PlaceUploadLogViewSet(ReadOnlyAccess, viewsets.ReadOnlyModelViewSet):
    queryset = PlaceUploadLog.objects.all()
    serializer_class = PlaceUploadLogSerializer


class AreaUploadLogViewSet(ReadOnlyAccess, viewsets.ReadOnlyModelViewSet):
    queryset = AreaUploadLog.objects.all()
    serializer_class = AreaUploadLogSerializer
