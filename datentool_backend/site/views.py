from rest_framework import viewsets, permissions

from .models import SiteSetting, ProjectSetting
from .serializers import SiteSettingSerializer, ProjectSettingSerializer


class ProjectSettingViewSet(viewsets.ModelViewSet):
    queryset = ProjectSetting.objects.all()
    serializer_class =  ProjectSettingSerializer


class SiteSettingViewSet(viewsets.ModelViewSet):
    #permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == 'default':
            return SiteSetting.objects.get_or_create(name='default')[0]

        return super().get_object()
