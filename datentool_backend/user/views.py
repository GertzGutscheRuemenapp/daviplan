from django.db.models import Q
from django.contrib.auth.models import User

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import(HasAdminAccessOrReadOnly,
                                                IsOwner
                                                )
from .permissions import CanUpdateProcessPermission, CanEditScenarioPermission
from .serializers import (UserSerializer,
                          PlanningProcessSerializer,
                          ScenarioSerializer
                          )
from datentool_backend.models import PlanningProcess, Scenario


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [HasAdminAccessOrReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()

    @action(methods=['GET', 'POST', 'PATCH', 'DELETE'], detail=True,
            permission_classes=[IsOwner])
    def usersettings(self, request, **kwargs):
        '''
        retrieve or set settings stored as json at profile object
        can be filtered by passing 'keys' query parameter
        '''
        profile = self.get_object().profile
        data = {}
        if request.data:
            # query dicts wrap all values in lists
            # workaround: assume that single values in lists were originally
            # not send as lists
            data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v
                    for k, v in dict(request.data).items()}

        if request.method == 'POST':
            profile.settings = data
        if request.method == 'PATCH':
            profile.settings.update(data)
        if request.method == 'DELETE':
            profile.settings = {}
        if request.method != 'GET':
            profile.save()

        if 'keys' in request.query_params:
            keys = request.query_params.get('keys').split(',')
            settings = { k: profile.settings[k] for k in keys }
        else:
            settings = profile.settings

        return Response(settings)


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

        return qs.filter(condition_user_in_user | condition_owner_in_user)