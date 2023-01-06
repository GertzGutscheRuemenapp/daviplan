import subprocess
import urllib.request
import requests
import os
import json

from django.db.models import Q
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse

from datentool_backend.utils.serializers import MessageSerializer
from datentool_backend.utils.routers import OSRMRouter
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 CanEditBasedata)
from datentool_backend.utils.processes import RunProcessMixin, ProcessScope
from datentool_backend.utils.raw_delete import delete_chunks

from datentool_backend.site.models import ProjectSetting
from datentool_backend.indicators.models import (MatrixCellStop,
                                                 MatrixStopStop,
                                                 MatrixPlaceStop,
                                                 MatrixCellPlace,
                                                 Stop,
                                                 )

from .models import Network, ModeVariant, Mode
from .serializers import NetworkSerializer, ModeVariantSerializer

import logging

logger = logging.getLogger('routing')

_l_i = 0

class ModeVariantViewSet(RunProcessMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        msg_start = f'Löschen der Variante {instance.label} gestartet'
        msg_end = f'Löschen der Variante {instance.label} beendet'
        response = self.run_sync_or_async(func=delete_depending_matrices,
                                          user=request.user,
                                          scope=ProcessScope.ROUTING,
                                          message_async=msg_start,
                                          message_sync=msg_end,
                                          ret_status=status.HTTP_204_NO_CONTENT,
                                          variant=instance)
        instance.delete()
        return response


def delete_depending_matrices(variant: ModeVariant,
                              logger: logging.Logger,
                              only_with_stops: bool = False):
    """
    Delete the depending objects in the matrices
    in the database first to improve performance
    """

    qs = MatrixCellStop.objects\
        .select_related('stop')\
        .filter(stop__variant=variant)
    delete_chunks(qs, logger)

    qs = MatrixPlaceStop.objects\
        .select_related('stop')\
        .filter(Q(stop__variant=variant)
                | Q(access_variant=variant))
    delete_chunks(qs, logger)

    if not only_with_stops:
        qs = MatrixCellPlace.objects\
            .filter(Q(variant=variant)
                    | Q(access_variant=variant))
        delete_chunks(qs, logger)

    qs = MatrixStopStop.objects\
        .select_related('from_stop')\
        .select_related('to_stop')\
        .filter(Q(from_stop__variant=variant) |
                Q(to_stop__variant=variant))
    delete_chunks(qs, logger)

    qs = Stop.objects\
        .filter(variant=variant)
    delete_chunks(qs, logger)


class NetworkViewSet(RunProcessMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    @extend_schema(
        description='download latest germany osm network from geofabrik',
        request=inline_serializer(name='EmptySerializer', fields={}),
        responses={201: OpenApiResponse(MessageSerializer,
                                        'Download successful'),}
    )
    @action(methods=['POST'], detail=False)
    def pull_base_network(self, request, **kwargs):
        msg_start = 'Herunterladen des OSM-Pbf-Netzes gestarted'
        msg_end = 'Herunterladen des OSM-Pbf-Netzes beendet'
        return self.run_sync_or_async(func=self._pull_base_network,
                                      user=request.user,
                                      scope=ProcessScope.ROUTING,
                                      message_async=msg_start,
                                      message_sync=msg_end,
                                      )

    @staticmethod
    def _pull_base_network(logger: logging.Logger):
        fp = os.path.join(settings.MEDIA_ROOT, settings.BASE_PBF)
        if os.path.exists(fp):
            os.remove(fp)
        # ToDo: download in chunks to show progress (in logs)
        logger.info(f'Lade {settings.PBF_URL} herunter')
        def progress_hook(count, blockSize, totalSize):
            global _l_i
            percent = int(count * blockSize * 100 / totalSize)
            if percent > 0 and _l_i != percent and percent % 10 == 0:
                logger.info(f'{percent}% ({count * blockSize // 1024}kB/'
                            f'{totalSize // 1024}kB)')
                _l_i = percent

        (f, res) = urllib.request.urlretrieve(settings.PBF_URL, fp,
                                              reporthook=progress_hook)
        # ToDo: errors?

        fp_project = os.path.join(settings.MEDIA_ROOT, 'projectarea.pbf')
        if os.path.exists(fp_project):
            os.remove(fp_project)

        logger.info(f'OSM-Straßennetz erfolgreich heruntergeladen')

    @extend_schema(
        description=('extract project area pbf, build routers for each mode '
                     'and start them'),
        request=inline_serializer(name='EmptySerializer', fields={}),
        responses={201: OpenApiResponse(MessageSerializer,
                                        'Build successful'),
                   400: OpenApiResponse(MessageSerializer,
                                        'Bad request'),
                   500: OpenApiResponse(MessageSerializer,
                                        'Build failed')}
    )
    @action(methods=['POST'], detail=False)
    def build_project_network(self, request, **kwargs):
        project_area = ProjectSetting.load().project_area
        if not project_area:
            msg = 'Das Projektgebiet ist nicht definiert'
            logger.error(msg)
            return Response({'message': msg },
                            status=status.HTTP_400_BAD_REQUEST)

        fn_base_pbf = 'germany-latest.osm.pbf'
        fp_base_pbf = os.path.join(settings.MEDIA_ROOT, fn_base_pbf)
        if not os.path.exists(fp_base_pbf):
            msg = 'Das Basisnetz wurde noch nicht heruntergeladen'
            logger.error(msg)
            return Response({'message': msg },
                            status=status.HTTP_400_BAD_REQUEST)

        msg_start = 'Bau der Router gestartet'
        msg_end = 'Bau der Router beendet'
        return self.run_sync_or_async(func=self._build_project_network,
                                      user=request.user,
                                      scope=ProcessScope.ROUTING,
                                      message_async=msg_start,
                                      message_sync=msg_end,
                                      )

    @staticmethod
    def _build_project_network(logger: logging.Logger):
        fn_geojson_projectarea = 'projectarea.geojson'
        fn_base_pbf = 'germany-latest.osm.pbf'
        fn_target_pbf = 'projectarea.pbf'

        fp_project_json = os.path.join(settings.MEDIA_ROOT, fn_geojson_projectarea)
        fp_target_pbf = os.path.join(settings.MEDIA_ROOT, fn_target_pbf)

        for fp in fp_target_pbf, fp_project_json:
            if os.path.exists(fp):
                os.remove(fp)

        buffer = 30000
        logger.info('Verschneide das Straßennetz mit dem Projektgebiet und '
                    f'einem Buffer von {buffer/1000} km')
        project_area = ProjectSetting.load().project_area
        buffered = project_area.buffer(buffer)
        buffered.transform('EPSG: 4326')

        geojson = json.dumps({
            'type': 'Feature',
            'name': 'project_area',
            'crs': { 'type': 'name',
                     'properties': { 'name': 'EPSG:4326' } },
            'geometry': json.loads(buffered.geojson),
        })


        with open(fp_project_json, "w") as json_file:
            json_file.write(geojson)

        # execute the command in the media-root-folder to avoid problems with
        # filepaths

        cmd = ['osmium', 'extract', '-p', fn_geojson_projectarea,
               fn_base_pbf, '-o', fn_target_pbf]
        process = subprocess.run(cmd, cwd=settings.MEDIA_ROOT)

        if process.returncode != 0:
            msg = ('Verschneidung fehlgeschlagen. Das Projektgebiet konnte '
                   'nicht aus dem Basisnetz extrahiert werden')
            logger.error(msg)
            raise Exception(msg)

        network, created = Network.objects.get_or_create(is_default=True)
        network.network_file = fp_target_pbf
        network.save()

        def build(mode):
            logger.info(f'Baue Router {mode.name}')
            router = OSRMRouter(mode)
            try:
                success = router.build(fp_target_pbf)
            except requests.exceptions.ConnectionError:
                success = False
            if not success:
                msg = (f'Berechnung fehlgeschlagen. Der Router {mode.name} '
                       'konnte nicht gebaut werden.')
                raise Exception(msg)
            else:
                msg = (f'Router {mode.name} erfolgreich gebaut.')
                logger.info(msg)
                router.run()

        modes = [Mode.WALK, Mode.BIKE, Mode.CAR]
        for mode in modes:
            build(mode)

    @extend_schema(
        description=('start routers for modes bike, car and foot'),
        request=inline_serializer(name='EmptySerializer', fields={}),
        responses={200: OpenApiResponse(MessageSerializer,
                                        'Build successful'),
                   500: OpenApiResponse(MessageSerializer,
                                        'Run failed')}
    )
    @action(methods=['POST'], detail=False)
    def run_routers(self, request, **kwargs):
        for mode in [Mode.CAR, Mode.BIKE, Mode.WALK]:
            router = OSRMRouter(mode)
            if router.is_running:
                continue
            success = router.run()
            if not success:
                return Response(
                    {'message': f'Failed to run router for mode {mode}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': f'Routers running'},
                        status=status.HTTP_200_OK)
