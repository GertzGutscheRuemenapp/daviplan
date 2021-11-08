from rest_framework import viewsets

from .models import (Mode)
from .serializers import (ModeSerializer)


class ModeViewSet(viewsets.ModelViewSet):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer
