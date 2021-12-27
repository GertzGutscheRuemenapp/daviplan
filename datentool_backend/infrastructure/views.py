from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from datentool_backend.utils.views import HasAdminAccessOrReadOnly, CanEditBasedata
from .models import (Infrastructure, FieldType, Service, Place, Capacity,
                     PlaceField, FClass, ScenarioCapacity, ScenarioPlace)
from .serializers import (InfrastructureSerializer, FieldTypeSerializer,
                          ServiceSerializer, PlaceSerializer,
                          CapacitySerializer, PlaceFieldSerializer,
                          FClassSerializer, ScenarioPlaceSerializer,
                          ScenarioCapacitySerializer)


#class CanPatchSymbol(permissions.BasePermission):
    #"""Permission Class for InfrastructureViewSet, patch of symbol, if user is authenticated """
    #def has_permission(self, request, view):
        #if request.user.is_authenticated and (
            #request.method in permissions.SAFE_METHODS or
            #request.user.is_superuser):
            #return True

    #def has_object_permission(self, request, view, obj):
        #if request.user.is_superuser:
            #return True
        #if (request.user.is_authenticated and
            #request.method in permissions.SAFE_METHODS):
            #return True
        #if (request.user.profile.can_edit_basedata and
            #request.method in ('PATCH')):
            #symbol = get_object_or_404(self.get_queryset(), symbol=self.kwargs["symbol"])
            #return symbol


    #def has_object_permission(self, request, view, obj):
        #if (request.user.profile.can_edit_basedata):
            #if (request.method in ('PATCH') and request.symbol == obj.symbol):
                #return request.user.profile.can_edit_basedata


class InfrastructureViewSet(viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
    #permission_classes = [HasAdminAccessOrReadOnly | CanPatchSymbol]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ScenarioPlaceViewSet(viewsets.ModelViewSet):
    queryset = ScenarioPlace.objects.all()
    serializer_class = ScenarioPlaceSerializer
    #permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class CapacityViewSet(viewsets.ModelViewSet):
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ScenarioCapacityViewSet(viewsets.ModelViewSet):
    queryset = ScenarioCapacity.objects.all()
    serializer_class = ScenarioCapacitySerializer
    #permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class FieldTypeViewSet(viewsets.ModelViewSet):
    queryset = FieldType.objects.all() # prefetch_related('classification_set',
                                         #         to_attr='classifications')
    serializer_class = FieldTypeSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class FClassViewSet(viewsets.ModelViewSet):
    queryset = FClass.objects.all()
    serializer_class = FClassSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PlaceFieldViewSet(viewsets.ModelViewSet):
    queryset = PlaceField.objects.all()
    serializer_class = PlaceFieldSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
