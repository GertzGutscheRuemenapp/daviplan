from rest_framework import viewsets, permissions
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from django.contrib.auth.models import User

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import(CanEditBasedata,
                                                HasAdminAccessOrReadOnly,
                                                IsOwner
                                                )

from .permissions import CanCreateProcessPermission, CanPatchSymbol

from .serializers import (UserSerializer,
                          YearSerializer,
                          PlanningProcessSerializer,
                          InfrastructureSerializer,
                          ServiceSerializer,
                          )
from .models import (Year,
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


@extend_schema_view(list=extend_schema(
    parameters=[
        OpenApiParameter(name='prognosis', required=False, type=int,
                         description='only years defined for prognosis with this pkey'),
        OpenApiParameter(name='with_population', required=False, type=bool ,
                         description='if true, only years where population data is available'),
    ]
))
class YearViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    serializer_class = YearSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        """ get the years. Request-parameters with_prognosis/with_population """
        qs = Year.objects.all()
        prognosis = self.request.query_params.get('prognosis')
        with_population = self.request.query_params.get('with_population')

        if with_population:
            expr = Q(population__isnull=False) & Q(population__prognosis__isnull=True)
            qs = qs.filter(expr)
        elif prognosis:
            expr = Q(population__isnull=False) & Q(population__prognosis_id=prognosis)
            qs = qs.filter(expr)
        return qs


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
