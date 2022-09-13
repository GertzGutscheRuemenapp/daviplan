from rest_framework import viewsets

from datentool_backend.utils.permissions import ReadOnlyPermission
from .models import LogEntry
from .serializers import LogEntrySerializer


class LogViewSet(viewsets.ReadOnlyModelViewSet):
     queryset = LogEntry.objects.all()
     serializer_class = LogEntrySerializer
     permission_classes = [ReadOnlyPermission]
     filterset_fields = ['room']
