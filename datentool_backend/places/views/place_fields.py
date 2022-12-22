from rest_framework import viewsets
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 CanEditBasedata,
                                                 )

from datentool_backend.places.models import PlaceField
from datentool_backend.places.serializers import PlaceFieldSerializer


class PlaceFieldViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PlaceField.objects.all()
    serializer_class = PlaceFieldSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
