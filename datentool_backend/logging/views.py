from rest_framework import viewsets
from datentool_backend.utils.views import ReadOnlyEditBasedataAdminAccess

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)
from .serializers import (CapacityUploadLogSerializer, PlaceUploadLogSerializer,
                          AreaUploadLogSerializer)


class CapacityUploadLogViewSet(ReadOnlyEditBasedataAdminAccess, viewsets.ReadOnlyModelViewSet):
    queryset = CapacityUploadLog.objects.all()
    serializer_class = CapacityUploadLogSerializer


class PlaceUploadLogViewSet(ReadOnlyEditBasedataAdminAccess, viewsets.ReadOnlyModelViewSet):
    queryset = PlaceUploadLog.objects.all()
    serializer_class = PlaceUploadLogSerializer


class AreaUploadLogViewSet(ReadOnlyEditBasedataAdminAccess, viewsets.ReadOnlyModelViewSet):
    queryset = AreaUploadLog.objects.all()
    serializer_class = AreaUploadLogSerializer
