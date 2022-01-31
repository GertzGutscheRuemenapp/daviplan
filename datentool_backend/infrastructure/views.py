import json

from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata,)

from .permissions import CanEditScenarioPermission

from .models import (Scenario,
                     FieldType,
                     Place,
                     Capacity,
                     PlaceField,
                     )

from .serializers import (ScenarioSerializer,
                          PlaceSerializer,
                          PlaceUpdateAttributeSerializer,
                          CapacitySerializer,
                          PlaceFieldSerializer,
                          )


class ScenarioViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    permission_classes = [CanEditScenarioPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        condition_user_in_user = Q(planning_process__users__in=[self.request.user.profile])
        condition_owner_in_user = Q(planning_process__owner=self.request.user.profile)

        return qs.filter(condition_user_in_user | condition_owner_in_user)


class PlaceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):

    serializer_class = PlaceSerializer
    serializer_action_class = {'update_attributes': PlaceUpdateAttributeSerializer}
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_serializer_class(self):
        return self.serializer_action_class.get(self.action,
                                                super().get_serializer_class())

    def get_queryset(self):
        queryset = Place.objects.all()
        service = self.request.query_params.get('service')
        if service:
            queryset = queryset.filter(service_capacity=service).distinct()
        return queryset

    @action(methods=['PATCH', 'PUT'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def update_attributes(self, request, **kwargs):
        """
        route to update attributes of a place
        """
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance,
                                      data=request.data,
                                      partial=partial,
                                      context={'request': self.request, })
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class CapacityViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PlaceFieldViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PlaceField.objects.all()
    serializer_class = PlaceFieldSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def perform_destroy(self, instance):
        """check, if there are referenced attributes"""
        places = Place.objects.filter(infrastructure=instance.infrastructure)
        for place in places:
            attr_dict = json.loads(place.attributes)
            if instance.attribute in attr_dict:
                if self.use_protection:
                    msg = f'Cannot delete "{instance}" because {place} has the attributes {place.attributes} using it'
                    raise ProtectedError(msg, [place])
                attr_dict.pop(instance.attribute)
                place.attributes = json.dumps(attr_dict)
                place.save()
        instance.delete()
