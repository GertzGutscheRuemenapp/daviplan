from rest_framework import viewsets
from datentool_backend.utils.views import CanEditBasedataPermission, UserPassesTestMixin
from .models import (Infrastructure, FieldType, Service, Quota, Place, Capacity,
                     PlaceField, FClass)
from .serializers import (InfrastructureSerializer, FieldTypeSerializer,
                          ServiceSerializer, QuotaSerializer, PlaceSerializer,
                          CapacitySerializer, PlaceFieldSerializer,
                          FClassSerializer)


class InfrastructureViewSet(viewsets.ModelViewSet): # UserPassesTestMixin,
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer

    ##Permission for admin_access; user, who "can_edit_basedata" can only patch the symbol
    #def test_func(self):
        #if self.request.user.is_superuser == True:
            #return True
        #elif (self.request.method in ('PATCH')
              #and self.request.user.pk is not None
              #and self.request.user.profile.can_edit_basedata):
            #return True
        #else:
            #return (self.request.user.pk is not None
                    #and self.request.user.profile.admin_access)







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
