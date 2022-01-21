from rest_framework import viewsets, permissions
from django.db.models import Q
from django.contrib.auth.models import User

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import(CanEditBasedata,
                                                HasAdminAccessOrReadOnly,
                                                )

from .permissions import CanCreateProcessPermission, CanPatchSymbol

from .serializers import (UserSerializer,
                          YearSerializer,
                          PlanningProcessSerializer,
                          InfrastructureSerializer,
                          ServiceSerializer,
                          )
from .models import (Profile,
                     Year,
                     PlanningProcess,
                     Infrastructure,
                     Service,
                     )


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [HasAdminAccessOrReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()


class YearViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Year.objects.all()
    serializer_class = YearSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PlanningProcessViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PlanningProcess.objects.all()
    serializer_class = PlanningProcessSerializer
    permission_classes = [permissions.IsAuthenticated & CanCreateProcessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        condition_user_in_user = Q(users__in=[self.request.user.profile])
        condition_owner_in_user = Q(owner=self.request.user.profile)
        return qs.filter(condition_user_in_user |
                         condition_owner_in_user).distinct()


class InfrastructureViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
    permission_classes = [CanPatchSymbol]


class ServiceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
