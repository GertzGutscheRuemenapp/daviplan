import requests
from requests.exceptions import (MissingSchema, ConnectionError, HTTPError)
from django.views.generic import DetailView
from django.http import JsonResponse
from rest_framework import viewsets, permissions
from rest_framework.exceptions import (ParseError, NotFound, APIException)
from rest_framework.decorators import action
from url_filter.integrations.drf import DjangoFilterBackend
from owslib.wms import WebMapService
from vectortiles.postgis.views import MVTView, BaseVectorTileView

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .models import (MapSymbol,
                     LayerGroup,
                     WMSLayer,
                     AreaLevel,
                     Area,
                     FieldType,
                     FClass,
                     )
from .serializers import (MapSymbolSerializer,
                          LayerGroupSerializer,
                          WMSLayerSerializer,
                          AreaLevelSerializer,
                          AreaSerializer,
                          FieldTypeSerializer,
                          FClassSerializer,
                          )


class AreaLevelTileView(MVTView, DetailView):
    model = AreaLevel
    vector_tile_fields = ('id', 'area_level', 'attributes')

    def get_vector_tile_layer_name(self):
        return self.get_object().name

    def get_vector_tile_queryset(self):
        return self.get_object().area_set.all()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return BaseVectorTileView.get(self, request=request, z=kwargs.get('z'),
                                      x=kwargs.get('x'), y=kwargs.get('y'))


class MapSymbolsViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class LayerGroupViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
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
        cors_enabled = ('access-control-allow-origin' in res.headers and
                        res.headers['access-control-allow-origin'] == '*')

        return JsonResponse({
            'version': wms.version,
            'layers': layers,
            'url': wms.url,
            'cors': cors_enabled
        })


class ProtectPresetPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # presets can not be deleted and name and source type (except date)
        # can not be changed
        if (obj.is_preset and
            (
                request.method == 'DELETE' or
                'name' in request.data or
                (
                    'source' in request.data and
                    set(request.data['source']) > set(['date'])
                )
            )):
            return False
        return True


class AreaLevelViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = AreaLevel.objects.all()
    serializer_class = AreaLevelSerializer
    permission_classes = [ProtectPresetPermission &
                          (HasAdminAccessOrReadOnly | CanEditBasedata)]


class AreaViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class FieldTypeViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = FieldType.objects.all()  # prefetch_related('classification_set',
                                         #         to_attr='classifications')
    serializer_class = FieldTypeSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class FClassViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = FClass.objects.all()
    serializer_class = FClassSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


