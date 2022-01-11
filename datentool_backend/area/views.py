from rest_framework import viewsets
from url_filter.integrations.drf import DjangoFilterBackend
from rest_framework.exceptions import (ParseError, NotFound, APIException,
                                       PermissionDenied)
from rest_framework.decorators import action
from django.http import JsonResponse
from owslib.wms import WebMapService
from requests.exceptions import (MissingSchema, ConnectionError,
                                        HTTPError)

from datentool_backend.utils.views import (CanEditBasedata,
                                           HasAdminAccessOrReadOnly)
from .models import (MapSymbol, LayerGroup, WMSLayer,
                     InternalWFSLayer, Source, AreaLevel, Area)
from .serializers import (MapSymbolsSerializer,
                          LayerGroupSerializer, WMSLayerSerializer,
                          InternalWFSLayerSerializer, SourceSerializer,
                          AreaLevelSerializer, AreaSerializer)


class MapSymbolsViewSet(viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolsSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class LayerGroupViewSet(viewsets.ModelViewSet):
    queryset = LayerGroup.objects.all()
    serializer_class = LayerGroupSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['external']


class WMSLayerViewSet(viewsets.ModelViewSet):
    queryset = WMSLayer.objects.all()
    serializer_class = WMSLayerSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_fields = ['active']

    @action(methods=['POST'], detail=False)
    def getcapabilities(self, request, **kwargs):
        user = request.user
        if not (user.is_authenticated or
                user.superuser or
                user.profile.admin_access or
                user.profile.can_edit_basedata):
            raise PermissionDenied
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
        return JsonResponse({
            'version': wms.version,
            'layers': layers,
            'url': wms.url
        })


class InternalWFSLayerViewSet(viewsets.ModelViewSet):
    queryset = InternalWFSLayer.objects.all()
    serializer_class = InternalWFSLayerSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AreaLevelViewSet(viewsets.ModelViewSet):
    queryset = AreaLevel.objects.all()
    serializer_class = AreaLevelSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
