from rest_framework import viewsets
from datentool_backend.utils.views import CanEditBasedataPermission
from .models import (DemandRateSet, DemandRate)
from .serializers import (DemandRateSetSerializer, DemandRateSerializer)


class DemandRateSetViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = DemandRateSet.objects.all()
    serializer_class = DemandRateSetSerializer


class DemandRateViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = DemandRate.objects.all()
    serializer_class = DemandRateSerializer