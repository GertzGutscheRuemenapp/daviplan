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
                                                 MatrixStopStop,
                                                 Router,
                                                 )
from datentool_backend.indicators.serializers import (StopSerializer,
                                                      UploadStopTemplateSerializer,
                                                      MatrixStopStopSerializer,
                                                      UploadMatrixStopStopTemplateSerializer,
                                                      RouterSerializer,
                          )


class ExcelTemplateMixin:
    """Mixin to download and upload excel-templates"""

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
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        qs = self.get_queryset()
        qs.delete()
        model = qs.model
        try:
            serializer = self.get_serializer()
            df = serializer.read_excel_file(request)

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
    serializer_action_classes = {'upload_template': UploadStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class MatrixStopStopViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    serializer_class = MatrixStopStopSerializer
    serializer_action_classes = {'upload_template': UploadMatrixStopStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixStopStop.objects.filter(variant=variant)


    @extend_schema(description='Upload Excel-File with Stops',
                   #parameters=[
                       #OpenApiParameter(name='drop_constraints',
                                        #required=False,
                                        #type=bool,
                                        #default=True,
                                        #description='set to false for tests'),
                       #OpenApiParameter(name='variant',
                                        #description='Mode variant',
                                        #required=True,
                                        #type=int),
                   #],
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        return super().upload_template(request)


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
