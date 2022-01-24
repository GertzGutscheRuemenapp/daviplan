from rest_framework import viewsets, permissions

from datentool_backend.utils.permissions import ReadOnlyPermission

from .models import (CapacityUploadLog,
                     PlaceUploadLog,
                     AreaUploadLog,
                     )
from .serializers import (CapacityUploadLogSerializer,
                          PlaceUploadLogSerializer,
                          AreaUploadLogSerializer,
                          )


class CapacityUploadLogViewSet(viewsets.ReadOnlyModelViewSet):
     queryset = CapacityUploadLog.objects.all()
     serializer_class = CapacityUploadLogSerializer
     permission_classes = [ReadOnlyPermission]


class PlaceUploadLogViewSet(viewsets.ReadOnlyModelViewSet):
     queryset = PlaceUploadLog.objects.all()
     serializer_class = PlaceUploadLogSerializer
     permission_classes = [ReadOnlyPermission]


class AreaUploadLogViewSet(viewsets.ReadOnlyModelViewSet):
     queryset = AreaUploadLog.objects.all()
     serializer_class = AreaUploadLogSerializer
     permission_classes = [ReadOnlyPermission]
