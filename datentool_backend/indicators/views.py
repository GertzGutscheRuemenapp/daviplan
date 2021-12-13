from rest_framework import viewsets

from datentool_backend.utils.views import CanEditBasedataPermission
from .models import (Mode, ModeVariant, ReachabilityMatrix, Router, Indicator)
from .serializers import (ModeSerializer, ModeVariantSerializer,
                          ReachabilityMatrixSerializer, RouterSerializer,
                          IndicatorSerializer)


class ModeViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer


class ModeVariantViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer


class ReachabilityMatrixViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = ReachabilityMatrix.objects.all()
    serializer_class = ReachabilityMatrixSerializer


class RouterViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer


class IndicatorViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
