from rest_framework import viewsets, permissions

from .models import SiteSetting, ProjectSetting, BaseDataSetting
from .serializers import (SiteSettingSerializer, ProjectSettingSerializer,
                          BaseDataSettingSerializer)
#from datentool_backend.utils.views import SingletonViewSet


class ProjectSettingViewSet(viewsets.ModelViewSet):
    queryset = ProjectSetting.objects.all()
    model_class = ProjectSetting
    serializer_class = ProjectSettingSerializer


class BaseDataSettingViewSet(viewsets.ModelViewSet):
    queryset = BaseDataSetting.objects.all()
    model_class = BaseDataSetting
    serializer_class = BaseDataSettingSerializer


class SiteSettingViewSet(viewsets.ModelViewSet):
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == 'default':
            return SiteSetting.objects.get_or_create(name='default')[0]

        return super().get_object()
