import warnings
from typing import Dict
import os
from tempfile import mktemp
import logging
logger = logging.getLogger('routing')

import pandas as pd

from rest_framework import viewsets

from django.db.models import Q
from django.contrib.gis.geos import Point

from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter)

from datentool_backend.utils.excel_template import (ExcelTemplateMixin,
                                                    write_template_df,
                                                    )

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from datentool_backend.indicators.models import (Stop,
                                                 MatrixCellStop,
                                                 MatrixStopStop,
                                                 MatrixPlaceStop)

from datentool_backend.indicators.serializers import (StopSerializer,
                                                      StopTemplateSerializer,
                                                      )

from datentool_backend.modes.views import delete_depending_matrices


class StopViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    serializer_action_classes = {'upload_template': StopTemplateSerializer,
                                 'create_template': StopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get(
            'variant', self.request.query_params.get('variant'))
        if variant is not None:
            return Stop.objects.filter(variant=variant)
        return Stop.objects.all()

    @extend_schema(
            parameters=[
                OpenApiParameter(name='variant', description='mode_variant_id',
                                 required=True, type=int),
            ],
        )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


    def get_read_excel_params(self, request) -> Dict:
        params = dict()
        logger.info('Speichere Eingangsdatei temporär auf Server')
        io_file = request.FILES['excel_file']
        ext = os.path.splitext(io_file.name)[-1]
        fp = mktemp(suffix=ext)
        with open(fp, 'wb') as f:
            f.write(io_file.file.read())
        params['excel_filepath'] = fp
        params['variant_id'] = request.data.get('variant')
        return params

    @staticmethod
    def process_excelfile(logger,
                          excel_filepath,
                          variant_id,
                          drop_constraints=False,
                          ):
        # read excelfile
        logger.info('Lese Excel-Datei')
        df = read_excel_file(excel_filepath, variant_id)
        df.name.fillna('-', inplace=True)
        os.remove(excel_filepath)

        # delete depending matrices before writing the dataframe
        delete_depending_matrices(variant_id, logger, only_with_stops=True)

        # write_df
        write_template_df(df, Stop, logger, drop_constraints=drop_constraints)

    def perform_destroy(self, instance):
        """
        Delete the depending objects in MatrixCellStop and MatrixStopStop
        in the database first to improve performance
        """
        stop_id = instance.pk
        qs = MatrixCellStop.objects.filter(stop=stop_id)
        qs.delete()

        qs = MatrixPlaceStop.objects.filter(stop=stop_id)
        qs.delete()

        qs = MatrixStopStop.objects.filter(Q(from_stop=stop_id) |
                                           Q(to_stop=stop_id))
        qs.delete()

        instance.delete()


def read_excel_file(excel_filepath, variant) -> pd.DataFrame:
    """read excelfile and return a dataframe"""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        df = pd.read_excel(excel_filepath,
                           sheet_name='Haltestellen',
                           skiprows=[1])

    # assert the stopnumers are unique
    assert df['HstNr'].is_unique, 'Haltestellennummer ist nicht eindeutig'

    # create points out of Lat/Lon and transform them to WebMercator
    points = [Point(stop['Lon'], stop['Lat'], srid=4326).transform(3857, clone=True)
              for i, stop in df.iterrows()]

    df2 = pd.DataFrame({'hstnr': df['HstNr'],
                        'name': df['HstName'],
                        'geom': points,
                        'variant_id': variant,
                        })
    return df2
