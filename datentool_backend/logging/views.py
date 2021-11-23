from rest_framework import viewsets

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)
from .serializers import (CapacityUploadLogSerializer, PlaceUploadLogSerializer,
                          AreaUploadLogSerializer)


class CapacityUploadLogViewSet(viewsets.ModelViewSet):
    queryset = CapacityUploadLog.objects.all()
    serializer_class = CapacityUploadLogSerializer


class PlaceUploadLogViewSet(viewsets.ModelViewSet):
    queryset = PlaceUploadLog.objects.all()
    serializer_class = PlaceUploadLogSerializer


class AreaUploadLogViewSet(viewsets.ModelViewSet):
    queryset = AreaUploadLog.objects.all()
    serializer_class = AreaUploadLogSerializer