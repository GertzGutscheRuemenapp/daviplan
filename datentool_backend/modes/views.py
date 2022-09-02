import subprocess
import urllib.request
import requests
import os
import json
import locale

from django.conf import settings
from django.core.serializers import serialize
from rest_framework import viewsets, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
from rest_framework.response import Response

from datentool_backend.utils.serializers import MessageSerializer
from datentool_backend.utils.routers import OSRMRouter
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.site.models import ProjectSetting

from .models import Network, ModeVariant, Mode
from .serializers import NetworkSerializer, ModeVariantSerializer

import logging

logger = logging.getLogger('routing')


class ModeVariantViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = ModeVariant.objects.all()
    serializer_class = ModeVariantSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    # fun fact: you can't write the method names in upper case, they have
    # to exactly match the ModelViewSet function names
    http_method_names = ('get', 'patch', 'head', 'options')


class NetworkViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
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
        fp = os.path.join(settings.MEDIA_ROOT, settings.BASE_PBF)
        if os.path.exists(fp):
            os.remove(fp)
        # ToDo: download in chunks to show progress (in logs)
        logger.info(f'Lade {settings.PBF_URL} herunter')
        self._d_i = 0
        def progress_hook(count, blockSize, totalSize):
            percent = int(count * blockSize * 100 / totalSize)
            if percent >= self._d_i * 10:
                logger.info(f'{percent}% ({count * blockSize // 1024}kB/'
                            f'{totalSize // 1024}kB)')
                self._d_i += 1

        (f, res) = urllib.request.urlretrieve(settings.PBF_URL, fp,
                                              reporthook=progress_hook)
        # ToDo: errors?

        fp_project = os.path.join(settings.MEDIA_ROOT, 'projectarea.pbf')
        if os.path.exists(fp_project):
            os.remove(fp_project)

        logger.info(f'OSM-Straßennetz erfolgreich heruntergeladen')
        return Response({'message': f'Download of base network successful'},
                        status=status.HTTP_201_CREATED)

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
        fp_project_json = os.path.join(settings.MEDIA_ROOT, 'projectarea.geojson')
        fp_base_pbf = os.path.join(settings.MEDIA_ROOT, 'germany-latest.osm.pbf')
        fp_target_pbf = os.path.join(settings.MEDIA_ROOT, 'projectarea.pbf')

        for fp in fp_target_pbf, fp_project_json:
            if os.path.exists(fp):
                os.remove(fp)
        project_area = ProjectSetting.load().project_area
        if not project_area:
            msg = 'Das Projektgebiet ist nicht definiert'
            logger.error(msg)
            return Response({'message': msg },
                            status=status.HTTP_400_BAD_REQUEST)

        buffer = 30000
        logger.info('Verschneide das Straßennetz mit dem Projektgebiet und '
                    f'einem Buffer von {buffer/1000} km')
        buffered = project_area.buffer(buffer)
        buffered.transform('EPSG: 4326')

        geojson = json.dumps({
            'type': 'Feature',
            'name': 'project_area',
            'crs': { 'type': 'name',
                     'properties': { 'name': 'EPSG:4326' } },
            'geometry': json.loads(buffered.geojson),
        })

        #geojson = serialize('geojson', ProjectSetting.objects.all(),
                            #geometry_field='project_area', fields=('id',))

        with open(fp_project_json, "w") as json_file:
            json_file.write(geojson)

        if os.name == 'nt':
            # osmium does not understand windows style paths at the -p argument,
            # other paths work, a bug i guess
            fp_project_json = os.path.splitdrive(
                fp_project_json)[1].replace(os.sep, '/')

        cmd = ['osmium', 'extract', '-p', fp_project_json,
               fp_base_pbf, '-o', fp_target_pbf]
        process = subprocess.run(cmd)
        if process.returncode != 0:
            msg = ('Verschneidung fehlgeschlagen. Das Projektgebiet konnte '
                   'nicht aus dem Basisnetz extrahiert werden')
            logger.error(msg)
            return Response(
                {'message': msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        network, created = Network.objects.get_or_create(is_default=True)
        network.network_file = fp_target_pbf
        network.save()

        modes = [Mode.CAR, Mode.BIKE, Mode.WALK]
        for mode in modes:
            logger.info(f'Baue Router {mode.name}')
            router = OSRMRouter(mode)
            try:
                success = router.build(fp_target_pbf)
            except requests.exceptions.ConnectionError:
                success = False
            if not success:
                msg = (f'Berechnung fehlgeschlagen. Der Router {mode.name} '
                       'konnte nicht gebaut werden.')
                return Response({'message': msg},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            router.run()

        msg = 'Router erfolgreich gebaut und gestartet'
        logger.info(msg)
        return Response({'message': msg}, status=status.HTTP_201_CREATED)

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
            success = OSRMRouter(mode).run()
            if not success:
                return Response(
                    {'message': f'Failed to run router for mode {mode}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': f'Routers running'},
                        status=status.HTTP_200_OK)
