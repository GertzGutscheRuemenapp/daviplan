import logging
logger = logging.getLogger('routing')

from typing import List

from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers

from drf_spectacular.utils import (extend_schema, inline_serializer,
                                   OpenApiResponse, OpenApiParameter)

from datentool_backend.utils.processes import (ProtectedProcessManager,
                                               ProcessScope)


from datentool_backend.indicators.compute.routing import (MatrixCellPlaceRouter,
                                                          MatrixCellStopRouter,
                                                          MatrixPlaceStopRouter,
                                                          TravelTimeRouterMixin,
                                                          )
from datentool_backend.utils.excel_template import ExcelTemplateMixin
from datentool_backend.utils.serializers import (MessageSerializer,
                                                 drop_constraints,
                                                 run_sync, )
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.utils.routers import OSRMRouter

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

from datentool_backend.indicators.serializers import (StopSerializer,
                                                      StopTemplateSerializer,
                                                      MatrixStopStopTemplateSerializer,
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


class MatrixStopStopViewSet(ExcelTemplateMixin,
                            viewsets.ModelViewSet):
    serializer_class = MatrixStopStopSerializer
    serializer_action_classes = {'upload_template': MatrixStopStopTemplateSerializer,
                                 'create_template': MatrixStopStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get(
            'variant', self.request.query_params.get('variant'))
        if variant is not None:
            return MatrixStopStop.objects.filter(variant=variant)
        return MatrixStopStop.objects.all()

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


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class TravelTimeRouterViewMixin(viewsets.GenericViewSet):
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    router: TravelTimeRouterMixin

    @extend_schema(description='Create Traveltime Matrix',
                   request=inline_serializer(
                       name='TravelTimeSerializer',
                       fields={
                           'drop_constraints': drop_constraints,
                           'run_sync': run_sync,
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
        run_sync = request.data.get('sync', False)
        variant_ids = request.data.get('variants', [])
        air_distance_routing = request.data.get('air_distance_routing', False)
        max_distance = request.data.get('max_distance')
        access_variant_id = request.data.get('access_variant')
        max_access_distance = request.data.get('max_access_distance')
        max_direct_walktime = request.data.get('max_direct_walktime')

        error_msg = None
        # run all routers on start
        for mode in [Mode.WALK, Mode.BIKE, Mode.CAR]:
            router = OSRMRouter(mode)
            if not router.service_is_up:
                error_msg = ('Der Router-Service reagiert nicht. '
                             'Bitte kontaktieren Sie den Administrator.')
                break
            if not router.is_running:
                router.run()
                error_msg = ('Der Router läuft gerade nicht. Er wird versucht '
                             'zu starten. Bitte warten Sie ein paar Minuten '
                             'und versuchen Sie es dann erneut')

        if error_msg:
            return Response({'Fehler': error_msg},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        places = request.data.get('places')
        logger.info('Starte Berechnung der Reisezeitmatrizen')

        with ProtectedProcessManager(
                request.user,
                scope=ProcessScope.ROUTING) as ppm:
            if not run_sync:
                ppm.run_async(self.calc,
                              self.router,
                              variant_ids,
                              places,
                              drop_constraints,
                              logger,
                              max_distance,
                              access_variant_id,
                              max_access_distance,
                              max_direct_walktime,
                              air_distance_routing,
                              )
            else:
                self.calc(
                    self.router,
                    variant_ids,
                    places,
                    drop_constraints,
                    logger,
                    max_distance,
                    access_variant_id,
                    max_access_distance,
                    max_direct_walktime,
                    air_distance_routing,
                )

        return Response({'message': 'Routenberechnung gestartet'},
                        status=status.HTTP_202_ACCEPTED)


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


class MatrixCellStopViewSet(TravelTimeRouterViewMixin):
    model = MatrixCellStop
    router = MatrixCellStopRouter


class MatrixPlaceStopViewSet(TravelTimeRouterViewMixin):
    model = MatrixPlaceStop
    router = MatrixPlaceStopRouter


class MatrixCellPlaceViewSet(TravelTimeRouterViewMixin):
    model = MatrixCellPlace
    router = MatrixCellPlaceRouter
