from django.db import transaction
from django.http.request import QueryDict
from io import StringIO
from distutils.util import strtobool
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse

from datentool_backend.utils.excel_template import ExcelTemplateMixin
from datentool_backend.utils.serializers import MessageSerializer, drop_constraints
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from datentool_backend.indicators.models import (Stop,
                                                 MatrixStopStop,
                                                 Router,
                                                 MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )
from datentool_backend.modes.models import ModeVariant, Mode, Network
from datentool_backend.indicators.serializers import (StopSerializer,
                                                      StopTemplateSerializer,
                                                      MatrixStopStopTemplateSerializer,
                                                      RouterSerializer,
                                                      MatrixCellPlaceSerializer,
                                                      MatrixCellStopSerializer,
                                                      MatrixPlaceStopSerializer,
                                                      MatrixRoutedCellPlaceSerializer,
                                                      MatrixRoutedCellStopSerializer,
                                                      MatrixRoutedPlaceStopSerializer,
                          )
from datentool_backend.utils.processes import ProtectedProcessManager


air_distance_routing = serializers.BooleanField(
        default=True,
        label='use air distance for routing',
        help_text='Set to False for network-based routing')


class StopViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    serializer_action_classes = {'upload_template': StopTemplateSerializer,
                                 'create_template': StopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return Stop.objects.filter(variant=variant)


class MatrixStopStopViewSet(ExcelTemplateMixin,
                            ProtectCascadeMixin,
                            viewsets.GenericViewSet):
    serializer_class = MatrixStopStopTemplateSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixStopStop.objects.filter(variant=variant)


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
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        with ProtectedProcessManager(request.user):
            return super().upload_template(request)


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class TravelTimeRouterMixin:
    serializer_classes = {}

    def get_serializer_class(self):
        air_distance_routing = bool(strtobool(
            self.request.data.get('air_distance_routing', 'True')))
        if air_distance_routing:
            return self.serializer_classes['air_distance']
        return self.serializer_classes['routed']

    @extend_schema(description='Create Traveltime Matrix',
                   request=inline_serializer(
                       name='TravelTimeSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'air_distance_routing': air_distance_routing,
                               'variant': serializers.PrimaryKeyRelatedField(
                                   queryset=ModeVariant.objects.all(),
                                   help_text='mode_variant_id',),
                           'access_variant': serializers.PrimaryKeyRelatedField(
                                   queryset=ModeVariant.objects.exclude(mode=Mode.TRANSIT),
                                   help_text='access_mode_variant_id',),
                           'speed': serializers.FloatField(),
                               'max_distance': serializers.FloatField(),
                               }
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Calculation successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Calculation failed')})
    @action(methods=['POST'], detail=False)
    def precalculate_traveltime(self, request):
        """Calculate traveltime with a air distance or network router"""
        serializer = self.get_serializer()
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
                df = serializer.calculate_traveltimes(request)

                with StringIO() as file:
                    df.to_csv(file, index=False)
                    file.seek(0)
                    model.copymanager.from_csv(
                        file,
                        drop_constraints=False, drop_indexes=False,
                    )

            except Exception as e:
                msg = str(e)
                return Response({'message': msg,}, status=status.HTTP_406_NOT_ACCEPTABLE)

            finally:
                # recreate indices
                if drop_constraints:
                    manager.restore_constraints()
                    manager.restore_indexes()

        msg = f'Traveltime Calculation successful, added {len(df)} rows'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


class MatrixCellPlaceViewSet(TravelTimeRouterMixin,
                             ProtectCascadeMixin,
                             viewsets.GenericViewSet):
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    serializer_classes = {'routed': MatrixRoutedCellPlaceSerializer,
                          'air_distance': MatrixCellPlaceSerializer,
                          }

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixCellPlace.objects.filter(variant=variant)

    @action(methods=['POST'], detail=False)
    def calculate_beelines(self, request):
        network, created = Network.objects.get_or_create(
            name='Basisnetz')
        network.is_default = True
        network.save()
        for mode in (Mode.WALK, Mode.BIKE, Mode.CAR):
            variant, created = ModeVariant.objects.get_or_create(
                network=network, mode=mode.value)
            data = QueryDict(mutable=True)
            data.update(self.request.data)
            data['drop_constraints'] = 'True'
            data['variant'] = variant.id
            request._full_data = data
            self.precalculate_traveltime(request)
        return Response({'message': 'Luftlinienberechnung abgeschlossen'},
                        status=status.HTTP_202_ACCEPTED)


class MatrixCellStopViewSet(TravelTimeRouterMixin,
                            ProtectCascadeMixin,
                            viewsets.GenericViewSet):
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    serializer_classes = {'routed': MatrixRoutedCellStopSerializer,
                          'air_distance': MatrixCellStopSerializer,
                          }

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixCellStop.objects.filter(variant=variant)


class MatrixPlaceStopViewSet(TravelTimeRouterMixin,
                             ProtectCascadeMixin,
                             viewsets.GenericViewSet):
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    serializer_classes = {'routed': MatrixRoutedPlaceStopSerializer,
                          'air_distance': MatrixPlaceStopSerializer,
                          }

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixPlaceStop.objects.filter(variant=variant)
