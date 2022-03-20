from django.http import HttpResponse
from io import StringIO
import pandas as pd
from distutils.util import strtobool
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


from datentool_backend.population.serializers import MessageSerializer
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


class ExcelTemplateMixin:
    """Mixin to download and upload excel-templates"""
    serializer_action_classes = {'upload_template': UploadStopTemplateSerializer,
                                 }

    def get_serializer_class(self):
        """get the serializer_class"""
        return self.serializer_action_classes.get(self.action, self.serializer_class)

    @action(methods=['GET'], detail=False)
    def download_template(self, request):
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

    @extend_schema(description='Upload Excel-File with Stops',
                   parameters=[
                       OpenApiParameter(name='drop_constraints',
                                        required=False,
                                        type=bool,
                                        default=True,
                                        description='set to false for tests'),
                   ],
                   #request=None,
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        self.queryset.delete()
        model = self.queryset.model
        try:
            excel_file = request.FILES['excel_file']
            serializer = self.get_serializer()
            df = serializer.read_excel_file(excel_file)

            drop_constraints = bool(strtobool(
                request.data.get('drop_constraints', 'False')))

            with StringIO() as file:
                df.to_csv(file, index=False)
                file.seek(0)
                model.copymanager.from_csv(
                    file,
                    drop_constraints=drop_constraints, drop_indexes=drop_constraints,
                )

        except Exception as e:
            msg = str(e)
            return Response({'message': msg,}, status=status.HTTP_406_NOT_ACCEPTABLE)

        msg = 'Upload successful'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


class StopViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]







class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
