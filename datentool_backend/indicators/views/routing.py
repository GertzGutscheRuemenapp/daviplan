import logging
logger = logging.getLogger('routing')
import warnings

import os
from typing import List, Dict
from tempfile import mktemp
from matrixconverters.read_ptv import ReadPTVMatrix

import pandas as pd
import numpy as np

from django.db.models import Q
from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers

from drf_spectacular.utils import (extend_schema, inline_serializer,
                                   OpenApiResponse, OpenApiParameter)

from datentool_backend.utils.processes import RunProcessMixin, ProcessScope

from datentool_backend.indicators.compute.routing import (MatrixCellPlaceRouter,
                                                          MatrixCellStopRouter,
                                                          MatrixPlaceStopRouter,
                                                          TravelTimeRouterMixin,
                                                          )
from datentool_backend.utils.excel_template import (ExcelTemplateMixin,
                                                    write_template_df,
                                                    )
from datentool_backend.utils.serializers import (MessageSerializer,
                                                 drop_constraints,
                                                 )
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.utils.routers import (OSRMRouter,
                                             assert_routers_are_running)
from datentool_backend.utils.raw_delete import delete_chunks

from datentool_backend.indicators.models import (Stop,
                                                 MatrixStopStop,
                                                 Router,
                                                 Place,
                                                 MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )

from datentool_backend.modes.models import (ModeVariant,
                                            Mode,
                                            )

from datentool_backend.indicators.serializers import (MatrixStopStopTemplateSerializer,
                                                      RouterSerializer,
                                                      MatrixStopStopSerializer
                                                      )


class RoutingError(Exception):
    """A Routing Error"""


air_distance_routing = serializers.BooleanField(
    default=False,
    label='use air distance for routing',
    help_text='Set to True for air-distance routing',
    required=False)


class MatrixStopStopViewSet(ExcelTemplateMixin,
                            viewsets.ModelViewSet):
    serializer_class = MatrixStopStopSerializer
    serializer_action_classes = {'upload_template': MatrixStopStopTemplateSerializer,
                                 'create_template': MatrixStopStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    @extend_schema(
            parameters=[
                OpenApiParameter(name='variant', description='mode_variant_id',
                                 required=True, type=int),
            ],
        )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    @extend_schema(description='Upload Excel-File or PTV-Visum-Matrix with Traveltimes from Stop to Stop',
                   request=inline_serializer(
                       name='FileDropConstraintModeVariantSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'variant': serializers.PrimaryKeyRelatedField(
                           queryset=ModeVariant.objects.all(),
                           help_text='mode_variant_id',),
                               'excel_or_visum_file': serializers.FileField(help_text='Excel- or PTV-Visum-Matrix'),
                               },
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False,
            parser_classes=[CamelCaseMultiPartParser])
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        return super().upload_template(request)

    def get_read_excel_params(self, request) -> Dict:
        params = dict()
        io_file = request.FILES['excel_or_visum_file']
        ext = os.path.splitext(io_file.name)[-1]
        logger.info('Lese Eingangsdatei')
        fp = mktemp(suffix=ext)
        with open(fp, 'wb') as f:
            f.write(io_file.file.read())
        params['excel_or_visum_filepath'] = fp

        params['variant_id'] = int(request.data.get('variant'))
        return params

    @staticmethod
    def process_excelfile(logger,
                          excel_or_visum_filepath,
                          variant_id,
                          drop_constraints=False,
                          ):
        # read excelfile
        logger.info('Lese Excel-Datei')
        df = read_traveltime_matrix(excel_or_visum_filepath, variant_id)

        # delete existing matrix entries if exist
        qs = MatrixStopStop.objects\
            .select_related('from_stop')\
            .select_related('to_stop')\
            .filter(Q(from_stop__variant=variant_id) |
                    Q(to_stop__variant=variant_id))
        delete_chunks(qs, logger)

        model = MatrixStopStop
        model_name = model._meta.object_name
        n_rows = len(df)
        model.add_n_rels_for_variant(variant_id, n_rows)
        logger.info(f'Schreibe insgesamt {n_rows:n} {model_name}-Einträge')
        stepsize = 100000
        for i in np.arange(0, n_rows, stepsize, dtype=np.int64):
            chunk = df.iloc[i:i + stepsize]
            n_inserted = len(chunk)
            write_template_df(chunk, model, logger, drop_constraints=drop_constraints)
            logger.info(f'{i + n_inserted:n}/{n_rows:n} {model_name}-Einträgen geschrieben')


def read_traveltime_matrix(excel_or_visum_filepath, variant_id) -> pd.DataFrame:
    """read excelfile and return a dataframe"""

    try:
        # get the values and unpivot the data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            df = pd.read_excel(excel_or_visum_filepath,
                               sheet_name='Reisezeit',
                               skiprows=[1])

    except ValueError as e:
        logger.info('Lese PTV-Matrix')
        da = ReadPTVMatrix(excel_or_visum_filepath)

        logger.info(f'PTV-Matrix mit den Dimensionen {da.dims}')

        df = da['matrix'].to_dataframe()
        df = df.loc[df['matrix']<999999]
        df.index.rename(['from_stop', 'to_stop'], inplace=True)
        df.rename(columns={'matrix': 'minutes',}, inplace=True)
        df.reset_index(inplace=True)

    finally:
        logger.info('Tempfile löschen')
        os.remove(excel_or_visum_filepath)

    # assert the stopnumbers are in stops
    logger.info('Überprüfe Haltestellennummern')
    cols = ['id', 'name', 'hstnr']
    df_stops = pd.DataFrame(Stop.objects.filter(variant=variant_id).values(*cols),
                            columns=cols)\
        .set_index('hstnr')
    assert df['from_stop'].isin(df_stops.index).all(), 'Von-Haltestelle nicht in Haltestellennummern'
    assert df['to_stop'].isin(df_stops.index).all(), 'Nach-Haltestelle nicht in Haltestellennummern'

    logger.info('Haltestellennummern der Matrix passen zu den hochgeladenen Haltestellen')
    df = df\
        .merge(df_stops['id'].rename('from_stop_id'),
                  left_on='from_stop', right_index=True)\
        .merge(df_stops['id'].rename('to_stop_id'),
                  left_on='to_stop', right_index=True)

    df = df[['from_stop_id', 'to_stop_id', 'minutes']]
    return df


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class TravelTimeRouterViewMixin(viewsets.GenericViewSet):
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    router: TravelTimeRouterMixin


    @staticmethod
    def calc(router_class: TravelTimeRouterMixin,
             variant_ids: List[int],
             places: List[int],
             drop_constraints: bool,
             logger: logging.Logger,
             max_distance: float = None,
             access_variant_id: int = None,
             max_access_distance: float = None,
             max_direct_walktime: float = None,
             air_distance_routing: bool = False,
             ):
        router = router_class()
        router.calc(variant_ids,
                    places,
                    drop_constraints,
                    logger,
                    max_distance,
                    access_variant_id,
                    max_access_distance,
                    max_direct_walktime,
                    air_distance_routing,
                    )


class MatrixCellPlaceViewSet(RunProcessMixin, TravelTimeRouterViewMixin):
    model = MatrixCellPlace
    router = MatrixCellPlaceRouter

    @extend_schema(description='Create Traveltime Matrix',
                   request=inline_serializer(
                       name='TravelTimeSerializer',
                       fields={
                           'drop_constraints': drop_constraints,
                           'air_distance_routing': air_distance_routing,
                           'variants': serializers.ListField(
                               child=serializers.PrimaryKeyRelatedField(
                                   queryset=ModeVariant.objects.all()
                               ),
                               help_text='mode_variant_ids',),
                            'places': serializers.ListField(
                                child=serializers.PrimaryKeyRelatedField(
                                    queryset=Place.objects.all()
                                ),
                                help_text='place_ids',
                                required=False),
                            'access_variant': serializers.PrimaryKeyRelatedField(
                               queryset=ModeVariant.objects.exclude(mode=Mode.TRANSIT),
                               help_text='access_mode_variant_id',
                               required=False),
                            'max_distance': serializers.FloatField(
                                help_text='Maximum distance in meters between source and destination',
                                required=False),
                            'max_access_distance': serializers.FloatField(
                                help_text='maximum distance in meters to next transit stops',
                                required=False
                            ),
                           'max_direct_walktime': serializers.FloatField(
                                help_text='direct walking time is taken instead '
                                'of transit time, if it is shorter '
                                'than the parameter `max_direct_walktime` in minutes',
                                required=False
                            ),
                       }
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Calculation successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Calculation failed')})
    @action(methods=['POST'], detail=False)
    def precalculate_traveltime(self, request):
        """Calculate traveltime with a air distance or network router"""
        drop_constraints = request.data.get('drop_constraints', False)
        variant_ids = request.data.get('variants', [])
        air_distance_routing = request.data.get('air_distance_routing', False)
        max_distance = request.data.get('max_distance')
        access_variant_id = request.data.get('access_variant')
        max_access_distance = request.data.get('max_access_distance')
        max_direct_walktime = request.data.get('max_direct_walktime')

        if not air_distance_routing:
            error_msg = assert_routers_are_running()

            if error_msg and not air_distance_routing:
                return Response({'Fehler': error_msg},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        places = request.data.get('places')
        logger.info('Starte Berechnung der Reisezeitmatrizen')

        msg_start = 'Routenberechnung gestartet'
        msg_end = 'Routenberechnung beendet'
        return self.run_sync_or_async(func=self.calc,
                                      user=request.user,
                                      scope=ProcessScope.ROUTING,
                                      drop_constraints=drop_constraints,
                                      message_async=msg_start,
                                      message_sync=msg_end,
                                      router_class=self.router,
                                      variant_ids=variant_ids,
                                      places=places,
                                      max_distance=max_distance,
                                      max_access_distance=max_access_distance,
                                      access_variant_id=access_variant_id,
                                      max_direct_walktime=max_direct_walktime,
                                      air_distance_routing=air_distance_routing,
                                      )


class TransitAccessRouterViewMixin(RunProcessMixin, TravelTimeRouterViewMixin):


    @extend_schema(description='Create Access Traveltime Matrix to Stops',
                   request=inline_serializer(
                       name='TravelTimeSerializer',
                       fields={
                           'drop_constraints': drop_constraints,
                           'air_distance_routing': air_distance_routing,
                           'transit_variant': serializers.PrimaryKeyRelatedField(
                                   queryset=ModeVariant.objects.filter(mode=Mode.TRANSIT),
                               help_text='transit_mode_variant_id',),
                            'places': serializers.ListField(
                                child=serializers.PrimaryKeyRelatedField(
                                    queryset=Place.objects.all()
                                ),
                                help_text='place_ids',
                                required=False),
                            'access_variant': serializers.PrimaryKeyRelatedField(
                               queryset=ModeVariant.objects.exclude(mode=Mode.TRANSIT),
                               help_text='access_mode_variant_id',
                               required=False),
                            'max_distance': serializers.FloatField(
                                help_text='Maximum distance in meters between source and destination',
                                required=False),
                            'max_access_distance': serializers.FloatField(
                                help_text='maximum distance in meters to next transit stops',
                                required=False
                            ),
                       }
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Calculation successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Calculation failed')})
    @action(methods=['POST'], detail=False)
    def precalculate_accesstime(self, request):
        """Calculate traveltime with a air distance or network router"""
        drop_constraints = request.data.get('drop_constraints', False)
        transit_variant_id = request.data.get('transit_variant')
        air_distance_routing = request.data.get('air_distance_routing', False)
        max_distance = request.data.get('max_distance')
        access_variant_id = request.data.get('access_variant')
        max_access_distance = request.data.get('max_access_distance')

        error_msg = assert_routers_are_running()

        if error_msg and not air_distance_routing:
            return Response({'Fehler': error_msg},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        variant_ids = [transit_variant_id]

        places = request.data.get('places')
        logger.info('Starte Berechnung der Reisezeitmatrizen')

        msg_start = 'Routenberechnung gestartet'
        msg_end = 'Routenberechnung beendet'
        return self.run_sync_or_async(func=self.calc,
                                      user=request.user,
                                      scope=ProcessScope.ROUTING,
                                      message_async=msg_start,
                                      message_sync=msg_end,
                                      router_class=self.router,
                                      variant_ids=variant_ids,
                                      drop_constraints=drop_constraints,
                                      places=places,
                                      max_distance=max_distance,
                                      max_access_distance=max_access_distance,
                                      access_variant_id=access_variant_id,
                                      air_distance_routing=air_distance_routing,
                                      )


class MatrixCellStopViewSet(TransitAccessRouterViewMixin):
    model = MatrixCellStop
    router = MatrixCellStopRouter


class MatrixPlaceStopViewSet(TransitAccessRouterViewMixin):
    model = MatrixPlaceStop
    router = MatrixPlaceStopRouter


