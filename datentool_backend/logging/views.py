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
          n_last = self.request.query_params.get('n_last')
          if room is not None:
               queryset = queryset.filter(room=room)
          # only possible options: DEBUG or INFO (DEBUG is everything anyway)
          if level == 'INFO':
               queryset = queryset.filter(level__in=['INFO', 'ERROR'])
          if n_last is not None:
               queryset = queryset.order_by('-date')[:int(n_last)][::-1]
          else:
               queryset = queryset.order_by('date')
          return queryset