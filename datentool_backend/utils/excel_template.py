from io import StringIO
from distutils.util import strtobool
import sys
import traceback
import logging

from django.http import HttpResponse
from django.db import transaction

from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse

from datentool_backend.utils.serializers import MessageSerializer, drop_constraints


class ColumnError(Exception):
    pass


class ExcelTemplateMixin:
    """Mixin to download and upload excel-templates"""
    serializer_action_classes = {}

    def get_serializer_class(self):
        """get the serializer_class"""
        return self.serializer_action_classes.get(self.action, self.serializer_class)

    @extend_schema(description='Create Excel-Template to download',
                   request=None,
                   #responses={
                       #(200, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'): bytes
                   #},
                   )

    @action(methods=['POST'], detail=False)
    def create_template(self, request, **kwargs):
        """Download the Template"""
        serializer = self.get_serializer()
        content = serializer.create_template(**kwargs)
        response = HttpResponse(
            content_type=(
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = \
            'attachment; filename=template.xlsx'
        response.write(content)
        return response

    @extend_schema(description='Upload Excel-File with Stops',
                   request=inline_serializer(
                       name='FileDropConstraintSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'excel_file': serializers.FileField(),
                               'variant': serializers.IntegerField(
                                   required=False,
                                   help_text='mode-variant id'),
                               }
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})

    @action(methods=['POST'], detail=False,
            parser_classes=[CamelCaseMultiPartParser])
    def upload_template(self, request, queryset=None, **kwargs):
        """Upload the filled out Template"""
        serializer = self.get_serializer()
        logger = serializer.logger or logging.getLogger(__name__)
        if queryset is None:
            queryset = serializer.get_queryset(request) \
                if hasattr(serializer, 'get_queryset') else self.get_queryset()
        model = queryset.model
        manager = model.copymanager
        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

            queryset.delete()

            try:
                logger.info('Lese Excel-Datei')
                df = serializer.read_excel_file(request, **kwargs)
                logger.info('Schreibe Daten in Datenbank')
                if len(df):
                    with StringIO() as file:
                        df.to_csv(file, index=False)
                        file.seek(0)
                        model.copymanager.from_csv(
                            file,
                            drop_constraints=False, drop_indexes=False,
                        )
            except ColumnError as e:
                msg = f'{e} Bitte überprüfen Sie das Template.'
                logger.error(msg)
                return Response({'Fehler': msg},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = repr(traceback.format_tb(exc_traceback))
                logger.error(msg)
                return Response({'Fehler': msg},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

            finally:
                # recreate indices
                if drop_constraints:
                    manager.restore_constraints()
                    manager.restore_indexes()

        if hasattr(serializer, 'post_processing'):
            serializer.post_processing(df, drop_constraints)

        msg = f'Upload von {len(df)} Einträgen erfolgreich'
        logger.info(msg)
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

