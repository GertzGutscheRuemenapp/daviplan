from rest_framework import viewsets

from .models import (Mode, ModeVariant)
from .serializers import (ModeSerializer, ModeVariantSerializer)


class ModeViewSet(viewsets.ModelViewSet):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer



class ModeVariantViewSet(viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer
