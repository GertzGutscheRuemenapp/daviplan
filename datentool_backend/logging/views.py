from rest_framework import viewsets, permissions
#from datentool_backend.utils.views import ReadOnlyAccess

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)
from .serializers import (CapacityUploadLogSerializer, PlaceUploadLogSerializer,
                          AreaUploadLogSerializer)


class ReadOnlyPermission(permissions.BasePermission):
     """Only user with admin_access or can_edit_basedata have read access to
     LogViewSets. Write access is forbidden
     """
     def has_permission(self, request, view):
          if not request.user.is_authenticated:
               return False
          if request.method in permissions.SAFE_METHODS and (
               request.user.is_superuser or
               request.user.profile.admin_access or
               request.user.profile.can_edit_basedata):
               return True
          return False


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
