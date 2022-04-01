from datentool_backend.utils.views import SingletonViewSet
from rest_framework import mixins, viewsets
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly,
    HasAdminAccessOrReadOnlyAny,
)
from rest_framework.response import Response

from .models import (SiteSetting,
                     ProjectSetting,
                     )
from .serializers import (SiteSettingSerializer,
                          ProjectSettingSerializer,
                          BaseDataSettingSerializer,
                          )


class ProjectSettingViewSet(SingletonViewSet):
    queryset = ProjectSetting.objects.all()
    model_class = ProjectSetting
    serializer_class = ProjectSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnly]


class BaseDataSettingViewSet(viewsets.GenericViewSet):
    serializer_class = BaseDataSettingSerializer
    def list(self, request):
        results = self.serializer_class({}, many=False).data
        return Response(results)


class SiteSettingViewSet(SingletonViewSet):
    queryset = SiteSetting.objects.all()
    model_class = SiteSetting
    serializer_class = SiteSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnlyAny]
    #authentication_classes = []

