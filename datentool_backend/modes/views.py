from rest_framework import viewsets

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .models import (Mode,
                     ModeVariant,
                     )
from .serializers import (ModeSerializer,
                          ModeVariantSerializer,
                          )


class ModeViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ModeVariantViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
