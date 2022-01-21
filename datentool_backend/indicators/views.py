from rest_framework import viewsets

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .models import (Mode,
                     ModeVariant,
                     Stop,
                     # ReachabilityMatrix,
                     Router,
                     Indicator,
                     )
from .serializers import (ModeSerializer,
                          ModeVariantSerializer,
                          StopSerializer,
                          # ReachabilityMatrixSerializer,
                          RouterSerializer,
                          IndicatorSerializer,
                          )


class ModeViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ModeVariantViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class StopViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


#class ReachabilityMatrixViewSet(viewsets.ModelViewSet):
    #queryset = ReachabilityMatrix.objects.all()
    #serializer_class = ReachabilityMatrixSerializer
    #permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
