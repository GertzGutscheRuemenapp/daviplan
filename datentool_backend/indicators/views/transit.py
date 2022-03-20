from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.decorators import action

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from datentool_backend.indicators.models import (Stop,
                                                 Router,
                                                 )
from datentool_backend.indicators.serializers import (StopSerializer,
                                                      RouterSerializer,
                                                      UploadStopTemplateSerializer,
                          )


class StopViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_action_classes = {'upload_template': UploadStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_serializer_class(self):
        """get the serializer_class"""
        return self.serializer_action_classes.get(self.action, StopSerializer)


    @action(methods=['GET'], detail=False)
    def download_template(self, request, **kwargs):
        """Download the Stops-Template"""
        serializer = self.get_serializer()
        content = serializer.create_template()
        response = HttpResponse(
            content_type=(
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = \
            'attachment; filename=template.xlsx'
        response.write(content)
        return response

    @action(methods=['POST'], detail=False)
    def upload_template(self):
        """Upload the filled out Stops-Template"""


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
