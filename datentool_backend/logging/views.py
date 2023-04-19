from rest_framework import viewsets

from datentool_backend.utils.permissions import ReadOnlyPermission
from .models import LogEntry
from .serializers import LogEntrySerializer


class LogViewSet(viewsets.ReadOnlyModelViewSet):
     queryset = LogEntry.objects.all()
     serializer_class = LogEntrySerializer
     permission_classes = [ReadOnlyPermission]

     def get_queryset(self):
          queryset = self.queryset
          level = self.request.query_params.get('level')
          room = self.request.query_params.get('room')
          if room is not None:
               queryset = queryset.filter(room=room)
          # only possible options: DEBUG or INFO (DEBUG is everything anyway)
          if level == 'INFO':
               queryset = queryset.filter(level__in=['INFO', 'ERROR'])
          return queryset
