from rest_framework import viewsets, permissions
from django.db.models import Q
from django.contrib.auth.models import User
from datentool_backend.utils.views import HasAdminAccessOrReadOnly
from .serializers import (UserSerializer, PlanningProcessSerializer,
                          ScenarioSerializer)
from .models import PlanningProcess, Scenario


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [HasAdminAccessOrReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()


class CanCreateProcessPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ('GET'):
            return True
        else:
            return request.user.profile.can_create_process

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET'):
            owner = obj.owner
            return request.user.profile == owner
        if request.method == 'POST':
            if request.user.is_superuser:
                return True
            if (request.user.profile.can_create_process and
                request.user.profile == obj.owner):
                return True


class PlanningProcessViewSet(viewsets.ModelViewSet):
    queryset = PlanningProcess.objects.all()
    serializer_class = PlanningProcessSerializer
    permission_classes = [permissions.IsAuthenticated & CanCreateProcessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user.profile)


class CanEditScenarioPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method == 'POST':
            if request.user.is_superuser:
                return True
            planning_process = PlanningProcess.objects.get(
                id=request.data.get('planning_process'))
            owner_is_user = request.user.profile == planning_process.owner
            user_in_users = request.user.profile in planning_process.users.all()
            allow_shared_change = planning_process.allow_shared_change
            return owner_is_user or (allow_shared_change and user_in_users)
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner_is_user = request.user.profile == obj.planning_process.owner
        user_in_users = request.user.profile in obj.planning_process.users.all()
        allow_shared_change = obj.planning_process.allow_shared_change
        return owner_is_user or (allow_shared_change and user_in_users)


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    permission_classes = [permissions.IsAuthenticated & CanEditScenarioPermission]


    def get_queryset(self):
        qs = super().get_queryset()
        condition_user_in_user = Q(planning_process__users__in=[self.request.user.profile])
        condition_owner_in_user = Q(planning_process__owner=self.request.user.profile)

        return qs.filter(condition_user_in_user | condition_owner_in_user)
