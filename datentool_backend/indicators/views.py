from rest_framework import viewsets

from .models import (Mode, ModeVariant, ReachabilityMatrix, Router, Indicator)
from .serializers import (ModeSerializer, ModeVariantSerializer,
                          ReachabilityMatrixSerializer, RouterSerializer,
                          IndicatorSerializer)


class ModeViewSet(viewsets.ModelViewSet):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer


class ModeVariantViewSet(viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer


class ReachabilityMatrixViewSet(viewsets.ModelViewSet):
    queryset = ReachabilityMatrix.objects.all()
    serializer_class = ReachabilityMatrixSerializer


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer


class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer