from abc import abstractstaticmethod, abstractmethod
from io import StringIO
from distutils.util import strtobool
from typing import Dict
import sys
import traceback
import pandas as pd
import logging

from django.http import HttpResponse
from django.db import transaction

from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from rest_framework import serializers
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse

from datentool_backend.utils.processes import RunProcessMixin
from datentool_backend.utils.serializers import MessageSerializer, drop_constraints
from datentool_backend.utils.permissions import HasAdminAccess, CanEditBasedata


class ColumnError(Exception):
    pass


class ExcelTemplateMixin(RunProcessMixin):
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

    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccess | CanEditBasedata])
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

        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))
        params = self.get_read_excel_params(request)

        return self.run_sync_or_async(func=self.process_excelfile,
                                      user=request.user,
                                      scope=serializer.scope,
                                      drop_constraints=drop_constraints,
                                      **params)

    @abstractstaticmethod
    def get_read_excel_params(self, request) -> Dict:
        """Read excel-params to a dict"""

    @abstractstaticmethod
    def process_excelfile(logger,
                          model,
                          drop_constraints=False,
                          **params):
        """Process the Excelfile"""
        # read excelfile -> df
        # write_template_df(df, model, logger, drop_constraints=drop_constraints)
        # postprocess (optional)


def write_template_df(df: pd.DataFrame, model, logger, drop_constraints=False,
                      log_level=logging.INFO):
    manager = model.copymanager
    with transaction.atomic():
        if drop_constraints:
            manager.drop_constraints()
            manager.drop_indexes()
        try:
            if len(df):
                logger.debug('Schreibe Daten in Datenbank')
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
            msg_df = f'''
            try to save DataFrame
            {df}
            columns: {df.columns}
            dtypes: {df.dtypes}
            shape: {df.shape}
            first_row: {df.iloc[0]}
            last_row: {df.iloc[-1]}
            to model {model._meta.object_name}
            with columns {model._meta.fields}
            '''
            msg = msg + msg_df
            logger.error(msg)
            raise Exception(msg)

        finally:
            # recreate indices
            if drop_constraints:
                manager.restore_constraints()
                manager.restore_indexes()

    if (len(df)):
        msg = f'{len(df):n} Einträge geschrieben'
        logger.log(log_level, msg)

