from django.db.models import Q

from rest_framework import viewsets, permissions

from datentool_backend.utils.views import ProtectCascadeMixin

from datentool_backend.places.permissions import (CanUpdateProcessPermission,
                                                  CanEditScenarioPermission)
from datentool_backend.places.serializers import (PlanningProcessSerializer,
                                                  ScenarioSerializer
                                                  )
from datentool_backend.places.models import PlanningProcess, Scenario


class PlanningProcessViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PlanningProcess.objects.all()
    serializer_class = PlanningProcessSerializer
    permission_classes = [permissions.IsAuthenticated &
                          CanUpdateProcessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        condition_user_in_user = Q(users__in=[self.request.user.profile])
        condition_owner_in_user = Q(owner=self.request.user.profile)
        return qs.filter(condition_user_in_user |
                         condition_owner_in_user).distinct()


class ScenarioViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    permission_classes = [CanEditScenarioPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        condition_user_in_user = Q(planning_process__users__in=[self.request.user.profile])
        condition_owner_in_user = Q(planning_process__owner=self.request.user.profile)
        shared_or_owned = qs.filter(condition_user_in_user |
                                    condition_owner_in_user)
        return shared_or_owned.distinct().order_by('id')
