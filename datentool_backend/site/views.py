from rest_framework import viewsets
from datentool_backend.utils.views import HasAdminAccessOrReadOnly, CanEditBasedata
from .models import SiteSetting, ProjectSetting, BaseDataSetting
from .serializers import (SiteSettingSerializer, ProjectSettingSerializer,
                          BaseDataSettingSerializer)
from datentool_backend.utils.views import SingletonViewSet


class ProjectSettingViewSet(SingletonViewSet):
    queryset = ProjectSetting.objects.all()
    model_class = ProjectSetting
    serializer_class = ProjectSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnly]


class BaseDataSettingViewSet(SingletonViewSet):
    queryset = BaseDataSetting.objects.all()
    model_class = BaseDataSetting
    serializer_class = BaseDataSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class SiteSettingViewSet(SingletonViewSet):
    queryset = SiteSetting.objects.all()
    model_class = SiteSetting
    serializer_class = SiteSettingSerializer
    permission_classes = [HasAdminAccessOrReadOnly]

