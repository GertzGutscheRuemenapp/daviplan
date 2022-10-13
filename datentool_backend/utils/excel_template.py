from io import StringIO
from distutils.util import strtobool
import sys
import traceback
import logging
import pandas as pd
from datentool_backend.utils.processes import (ProtectedProcessManager,
                                               ProcessScope)

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

    def upload_template(self, request, queryset=None, **kwargs):
        """Upload the filled out Template"""
        serializer = self.get_serializer()
        logger = getattr(serializer, 'logger', logging.getLogger(__name__))
        if queryset is None:
            queryset = serializer.get_queryset(request) \
                if hasattr(serializer, 'get_queryset') else self.get_queryset()
        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        try:
            logger.info('Lese Excel-Datei')
            df = serializer.read_excel_file(request, **kwargs)
        except ColumnError as e:
            msg = f'{e} Bitte überprüfen Sie das Template.'
            logger.error(msg)
            return Response({'Fehler': msg},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        with ProtectedProcessManager(
            request.user,
            scope=getattr(serializer, 'scope', ProcessScope.GENERAL)) as ppm:
            # workaround: if post requesting is required, do all the writing
            # of data before synchronously
            # did not manage to pass both into async
            if hasattr(serializer, 'post_processing'):
                self.write_template_df(df, queryset, logger,
                                       drop_constraints=drop_constraints)
                ppm.run_async(serializer.post_processing, df,
                              drop_constraints=drop_constraints)
            else:
                ppm.run_async(self.write_template_df, df, queryset, logger,
                              drop_constraints=drop_constraints)
        return Response({'message': 'Upload gestartet'},
                        status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def write_template_df(df: pd.DataFrame, queryset, logger, drop_constraints=False):
        model = queryset.model
        manager = model.copymanager
        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()
            logger.info(f'Lösche {len(queryset)} vorhandene Einträge')
            queryset.delete()
            try:
                if len(df):
                    logger.info('Schreibe Daten in Datenbank')
                    with StringIO() as file:
                        df.to_csv(file, index=False)
                        file.seek(0)
                        model.copymanager.from_csv(
                            file,
                            drop_constraints=False, drop_indexes=False,
                        )

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = repr(traceback.format_tb(exc_traceback))
                logger.error(msg)

            finally:
                # recreate indices
                if drop_constraints:
                    manager.restore_constraints()
                    manager.restore_indexes()

        msg = f'{len(df)} Einträge geschrieben'
        logger.info(msg)
