from rest_framework import viewsets
from datentool_backend.utils.views import CanEditBasedataPermission
from .models import (Infrastructure, FieldType, Service, Quota, Place, Capacity,
                     PlaceField, FClass)
from .serializers import (InfrastructureSerializer, FieldTypeSerializer,
                          ServiceSerializer, QuotaSerializer, PlaceSerializer,
                          CapacitySerializer, PlaceFieldSerializer,
                          FClassSerializer)


class InfrastructureViewSet(viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer


class QuotaViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Quota.objects.all()
    serializer_class = QuotaSerializer


class ServiceViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class PlaceViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer


class CapacityViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer


class FieldTypeViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = FieldType.objects.all() # prefetch_related('classification_set',
                                         #         to_attr='classifications')
    serializer_class = FieldTypeSerializer


class FClassViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = FClass.objects.all()
    serializer_class = FClassSerializer


class PlaceFieldViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = PlaceField.objects.all()
    serializer_class = PlaceFieldSerializer
