from rest_framework import viewsets

from .models import (Infrastructure, FieldType, Service, Quota, Place, Capacity,
                     PlaceField, FClass)
from .serializers import (InfrastructureSerializer, FieldTypeSerializer,
                          ServiceSerializer, QuotaSerializer, PlaceSerializer,
                          CapacitySerializer, PlaceFieldSerializer,
                          FClassSerializer)


class InfrastructureViewSet(viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer


class QuotaViewSet(viewsets.ModelViewSet):
    queryset = Quota.objects.all()
    serializer_class = QuotaSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer


class CapacityViewSet(viewsets.ModelViewSet):
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer


class FieldTypeViewSet(viewsets.ModelViewSet):
    queryset = FieldType.objects.all() # prefetch_related('classification_set',
                                         #         to_attr='classifications')
    serializer_class = FieldTypeSerializer


class FClassViewSet(viewsets.ModelViewSet):
    queryset = FClass.objects.all()
    serializer_class = FClassSerializer


class PlaceFieldViewSet(viewsets.ModelViewSet):
    queryset = PlaceField.objects.all()
    serializer_class = PlaceFieldSerializer
