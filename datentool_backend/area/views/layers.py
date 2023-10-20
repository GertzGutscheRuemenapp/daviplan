import requests
from requests.exceptions import (MissingSchema, ConnectionError, HTTPError)

from django.http import JsonResponse

from rest_framework import viewsets
from rest_framework.exceptions import (ParseError, NotFound, APIException)
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema

from owslib.wms import WebMapService

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (HasAdminAccessOrReadOnly,
                                                 CanEditBasedata)

from datentool_backend.area.models import MapSymbol, LayerGroup, WMSLayer

from datentool_backend.area.serializers import (MapSymbolSerializer,
                                                LayerGroupSerializer,
                                                WMSLayerSerializer,
                                                GetCapabilitiesRequestSerializer,
                                                GetCapabilitiesResponseSerializer,
                                                )


class MapSymbolsViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class LayerGroupViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = LayerGroup.objects.all()
    serializer_class = LayerGroupSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_fields = ['external']


class WMSLayerViewSet(viewsets.ModelViewSet):
    queryset = WMSLayer.objects.all()
    serializer_class = WMSLayerSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_fields = ['active']

    @extend_schema(
        description='Get capabilites of WMS-Service',
        request=GetCapabilitiesRequestSerializer,
        responses=GetCapabilitiesResponseSerializer,
    )
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def getcapabilities(self, request, **kwargs):
        url = request.data.get('url')
        version = request.data.get('version', '1.3.0')
        if not url:
            raise ParseError('keine URL angegeben')
        try:
            wms = WebMapService(url, version=version)
        except MissingSchema:
            raise ParseError(
                'ungültiges URL-Schema (http:// bzw. https:// vergessen?)')
        except ConnectionError:
            raise NotFound('URL nicht erreichbar')
        except HTTPError as e:
            raise APIException(str(e))
        except Exception:
            raise APIException('ein Fehler ist bei der Abfrage der '
                               'Capabilities aufgetreten')

        layers = []
        for layer_name, layer in wms.contents.items():
            layers.append({
                'name':  layer_name,
                'title': layer.title,
                'abstract': layer.abstract,
                'bbox': layer.boundingBoxWGS84,
            })

        # test for anonymous CORS-support
        headers = {
            "Origin": "*",
            "Referer": "*",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        res = requests.options(url, headers=headers)
        cors_enabled = (res.status_code == 200 and
                        ('access-control-allow-origin' in res.headers and
                        res.headers['access-control-allow-origin'] == '*'))

        return JsonResponse({
            'version': wms.version,
            'layers': layers,
            'url': wms.url,
            'cors': cors_enabled
        })
