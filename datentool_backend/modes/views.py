from rest_framework import viewsets

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .models import Network
from .serializers import NetworkSerializer


class NetworkViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
