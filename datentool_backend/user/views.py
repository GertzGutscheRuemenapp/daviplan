from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from datentool_backend.utils.permissions import(HasAdminAccessOrReadOnly,
                                                IsOwner
                                                )
from .serializers import UserSerializer


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
