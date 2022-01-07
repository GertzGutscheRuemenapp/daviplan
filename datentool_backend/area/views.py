from rest_framework import viewsets
from url_filter.integrations.drf import DjangoFilterBackend
from rest_framework.exceptions import ParseError
from rest_framework.decorators import action
from django.http import HttpResponse
import requests

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

    @action(methods=['POST'], detail=False)
    def proxy(self, request, **kwargs):
        url = request.data.get('url')
        if not url:
            raise ParseError()
        response = requests.get(url)
        content_type = response.headers['content-type']
        return HttpResponse(response.content, content_type=content_type,
                            status=response.status_code)


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
