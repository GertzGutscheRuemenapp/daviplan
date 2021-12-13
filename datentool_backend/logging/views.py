from rest_framework import viewsets

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)
from .serializers import (CapacityUploadLogSerializer, PlaceUploadLogSerializer,
                          AreaUploadLogSerializer)


class CapacityUploadLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CapacityUploadLog.objects.all()
    serializer_class = CapacityUploadLogSerializer


class PlaceUploadLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlaceUploadLog.objects.all()
    serializer_class = PlaceUploadLogSerializer


class AreaUploadLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AreaUploadLog.objects.all()
    serializer_class = AreaUploadLogSerializer
