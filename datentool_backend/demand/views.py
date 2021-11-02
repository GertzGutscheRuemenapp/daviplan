from rest_framework import viewsets

from .models import (DemandRateSet, DemandRate)
from .serializers import (DemandRateSetSerializer, DemandRateSerializer)


class DemandRateSetViewSet(viewsets.ModelViewSet):
    queryset = DemandRateSet.objects.all()
    serializer_class = DemandRateSetSerializer


class DemandRateViewSet(viewsets.ModelViewSet):
    queryset = DemandRate.objects.all()
    serializer_class = DemandRateSerializer