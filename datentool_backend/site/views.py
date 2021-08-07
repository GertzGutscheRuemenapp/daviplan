from rest_framework import viewsets

from .models import SiteSettings
from .serializers import SiteSettingsSerializer


class SiteSettingsViewSet(viewsets.ModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == 'default':
            return SiteSettings.objects.get_or_create(name='default')[0]

        return super().get_object()