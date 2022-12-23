from rest_framework import viewsets

from datentool_backend.utils.views import ProtectCascadeMixin

from datentool_backend.infrastructure.models import InfrastructureAccess, Infrastructure

from datentool_backend.infrastructure.permissions import CanPatchSymbol
from datentool_backend.infrastructure.serializers import InfrastructureSerializer


class InfrastructureViewSet(ProtectCascadeMixin,
                            viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
    permission_classes = [CanPatchSymbol]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Infrastructure.objects.all()
        try:
            profile = self.request.user.profile
        except AttributeError:
            # no profile yet
            return Infrastructure.objects.none()
        if profile.admin_access:
            return Infrastructure.objects.all()

        accessible = InfrastructureAccess.objects.filter(
            profile=profile).values_list('infrastructure__id')
        return Infrastructure.objects.filter(id__in=accessible)
