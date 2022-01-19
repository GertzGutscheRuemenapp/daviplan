from rest_framework import viewsets
from url_filter.integrations.drf import DjangoFilterBackend
from rest_framework.exceptions import (ParseError, NotFound, APIException,
                                       PermissionDenied)
from vectortiles.postgis.views import MVTView, BaseVectorTileView
from django.views.generic import DetailView
from rest_framework.decorators import action
from django.http import JsonResponse
from owslib.wms import WebMapService
from requests.exceptions import (MissingSchema, ConnectionError,
                                        HTTPError)

from datentool_backend.utils.views import (CanEditBasedata,
                                           HasAdminAccessOrReadOnly,
                                           ProtectCascadeMixin)

from .models import (MapSymbol, LayerGroup, WMSLayer,
                     InternalWFSLayer, Source, AreaLevel, Area)
from .serializers import (MapSymbolsSerializer,
                          LayerGroupSerializer, WMSLayerSerializer,
                          InternalWFSLayerSerializer, SourceSerializer,
                          AreaLevelSerializer, AreaSerializer)

from gisserver.features import FeatureType, ServiceDescription, field
from gisserver.geometries import CRS, WGS84
from gisserver.views import WFSView
RD_NEW = CRS.from_srid(3857)


class AreaLevelWFSView(WFSView):

    xml_namespace = "http://example.org/gisserver"

    # The service metadata
    service_description = ServiceDescription(
        title="Places",
        abstract="Unittesting",
        keywords=["django-gisserver"],
        provider_name="Django",
        provider_site="https://www.example.com/",
        contact_person="django-gisserver",
    )
    feature_types = [
        FeatureType(
            Area.objects.all(),
            fields=["id",
                    field("arealevel.name", model_attribute="area_level")],
            other_crs=[RD_NEW]
        ),
    ]

class AreaLevelTileView(MVTView, DetailView):
    model = AreaLevel

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
    serializer_class = MapSymbolsSerializer
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
        return JsonResponse({
            'version': wms.version,
            'layers': layers,
            'url': wms.url
        })


class InternalWFSLayerViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = InternalWFSLayer.objects.all()
    serializer_class = InternalWFSLayerSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class SourceViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AreaLevelViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = AreaLevel.objects.all()
    serializer_class = AreaLevelSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AreaViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
