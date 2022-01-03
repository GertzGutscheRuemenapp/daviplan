from rest_framework import viewsets

from datentool_backend.utils.views import HasAdminAccessOrReadOnly, CanEditBasedata
from .models import (Mode, ModeVariant, ReachabilityMatrix, Router, Indicator)
from .serializers import (ModeSerializer, ModeVariantSerializer,
                          ReachabilityMatrixSerializer, RouterSerializer,
                          IndicatorSerializer)


class ModeViewSet(viewsets.ModelViewSet):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ModeVariantViewSet(viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ReachabilityMatrixViewSet(viewsets.ModelViewSet):
    queryset = ReachabilityMatrix.objects.all()
    serializer_class = ReachabilityMatrixSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
