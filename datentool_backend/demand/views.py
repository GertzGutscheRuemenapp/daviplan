from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .constants import RegStatAgeGroups, RegStatAgeGroup
from .models import (AgeGroup, Gender, DemandRateSet, DemandRate)
from .serializers import (GenderSerializer,
                          AgeGroupSerializer,
                          DemandRateSetSerializer,
                          DemandRateSerializer)


class GenderViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AgeGroupViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = AgeGroup.objects.all().order_by('from_age')
    serializer_class = AgeGroupSerializer
    permission_classes = [HasAdminAccessOrReadOnly]

    def list(self, request, *args, **kwargs):
        # return the default age-groups (Regionalstatistik) when query parameter
        # ?defaults is set to true
        show_defaults = request.query_params.get('defaults')
        if show_defaults and show_defaults.lower() == 'true':
            res = [{'fromAge': a.from_age, 'toAge': a.to_age,
                    'code': a.code, 'label': a.name}
                   for a in RegStatAgeGroups.agegroups]
            return Response(res)
        return super().list(request, *args, **kwargs)

    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def replace(self, request, **kwargs):
        AgeGroup.objects.all().delete()
        for a in request.data:
            g = AgeGroup(from_age=a['from_age'], to_age=a['to_age'])
            g.save()
        return self.list(request)

    @action(methods=['POST'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def check(self, request, **kwargs):
        """
        route to compare posted age-groups with default age-groups
        (Regionalstatistik) in any order
        """
        try:
            age_groups = [RegStatAgeGroup(a['from_age'], a['to_age'])
                          for a in request.data]
        except KeyError:
            raise ParseError()
        valid = RegStatAgeGroups.check(age_groups)
        return Response({'valid': valid})


class DemandRateSetViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = DemandRateSet.objects.all()
    serializer_class = DemandRateSetSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class DemandRateViewSet(viewsets.ModelViewSet):
    queryset = DemandRate.objects.all()
    serializer_class = DemandRateSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

