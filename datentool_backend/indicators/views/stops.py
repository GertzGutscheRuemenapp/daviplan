import warnings
from typing import Dict
import pandas as pd

from rest_framework import viewsets

from django.contrib.gis.geos import Point

from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter)

from datentool_backend.utils.excel_template import (ExcelTemplateMixin,
                                                    write_template_df,
                                                    )

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from datentool_backend.indicators.models import Stop

from datentool_backend.indicators.serializers import (StopSerializer,
                                                      StopTemplateSerializer,
                                                      )


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
        params['excel_file'] = request.FILES['excel_file']
        params['variant_id'] = request.data.get('variant')
        return params

    @staticmethod
    def process_excelfile(queryset,
                          logger,
                          excel_file,
                          variant_id,
                          drop_constraints=False,
                          ):
        # read excelfile
        logger.info('Lese Excel-Datei')
        df = read_excel_file(excel_file, variant_id)

        # write_df
        write_template_df(df, queryset, logger, drop_constraints=drop_constraints)


def read_excel_file(excel_file, variant) -> pd.DataFrame:
    """read excelfile and return a dataframe"""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        df = pd.read_excel(excel_file.file,
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
