from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from datentool_backend.utils.views import (HasAdminAccessOrReadOnly,
                                           CanEditBasedata,
                                           ProtectCascadeMixin)
from datentool_backend.user.views import CanEditScenarioPermission

from .models import (Infrastructure, FieldType, Service, Place, Capacity,
                     PlaceField, FClass, ScenarioCapacity, ScenarioPlace)

from .serializers import (InfrastructureSerializer, FieldTypeSerializer,
                          ServiceSerializer, PlaceSerializer,
                          CapacitySerializer, PlaceFieldSerializer,
                          FClassSerializer, ScenarioPlaceSerializer,
                          ScenarioCapacitySerializer)


class CanPatchLayer(permissions.BasePermission):
    """Permission Class for InfrastructureViewSet, patch of symbol, if user is
    authenticated and can edit basedata """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.profile.admin_access:
            return True
        if request.method in ['PATCH'] + list(permissions.SAFE_METHODS):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if (request.user.is_superuser or request.user.profile.admin_access or
            request.method in permissions.SAFE_METHODS):
            return True
        if (request.user.profile.can_edit_basedata and
            request.method in ('PATCH',) and (
                        len(request.data.keys()) == 0 or
                        set(request.data.keys()) <= set(['layer'])
                )
        ):
            return True
        return False


class InfrastructureViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
    permission_classes = [CanPatchLayer]


class ServiceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PlaceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ScenarioPlaceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = ScenarioPlace.objects.all()
    serializer_class = ScenarioPlaceSerializer
    #permission_classes = [CanEditScenarioPermission]


class CapacityViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class ScenarioCapacityViewSet(viewsets.ModelViewSet):
    queryset = ScenarioCapacity.objects.all()
    serializer_class = ScenarioCapacitySerializer
    #permission_classes = [CanEditScenarioPermission]


class FieldTypeViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
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
