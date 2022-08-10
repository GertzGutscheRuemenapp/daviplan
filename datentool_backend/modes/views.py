import subprocess
import urllib.request
import requests
import os
import json

from django.conf import settings
from django.core.serializers import serialize
from rest_framework import viewsets, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
from rest_framework.response import Response

from datentool_backend.utils.serializers import MessageSerializer
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.site.models import ProjectSetting

from .models import Network, ModeVariant
from .serializers import NetworkSerializer, ModeVariantSerializer


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
        (f, res) = urllib.request.urlretrieve(settings.PBF_URL, fp)
        # ToDo: errors?
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
            return Response(
                {'message': f'Project Area is undefined'},
                status=status.HTTP_400_BAD_REQUEST)

        #geojson = json.dumps({
            #'type': 'Feature',
            #'name': 'project_area',
            #'crs': { 'type': 'name',
                     #'properties': { 'name': 'urn:ogc:def:crs:EPSG::3857' } },
            #'geometry': json.loads(project_area.geojson),
        #})

        geojson = serialize('geojson', ProjectSetting.objects.all(),
                            geometry_field='project_area', fields=('id',))

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
            return Response(
                {'message': f'Build failed. Could not extract '
                 'Project area from base network'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        baseurl = f'http://{settings.ROUTING_HOST}:{settings.ROUTING_PORT}'
        # ToDo: use own route to run and build to test
        for mode in ['car', 'bicycle', 'foot']:
            files = {'file': open(fp_target_pbf, 'rb')}
            res = requests.post(f'{baseurl}/build/{mode}', files=files)
            if res.status_code != 200:
                return Response({'message': f'Build failed. Could not build '
                                 f'router network {mode}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            requests.post(f'{baseurl}/run/{mode}')

        return Response({'message': f'Networks successfully built and running'},
                        status=status.HTTP_201_CREATED)

    @extend_schema(
        description=('start routers for modes bike, car and foot'),
        request=inline_serializer(name='EmptySerializer', fields={}),
        responses={200: OpenApiResponse(MessageSerializer,
                                        'Build successful'),
                   500: OpenApiResponse(MessageSerializer,
                                        'Run failed')}
    )
    @action(methods=['POST'], detail=False)
    def run_router(self, request, **kwargs):
        baseurl = f'http://{settings.ROUTING_HOST}:{settings.ROUTING_PORT}'
        for mode in ['car', 'bicycle', 'foot']:
            res = requests.post(f'{baseurl}/run/{mode}')
            if res.status_code != 200:
                return Response(
                    {'message': f'Failed to run router for mode {mode}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': f'Routers running'},
                        status=status.HTTP_200_OK)
