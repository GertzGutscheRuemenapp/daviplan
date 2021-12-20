from rest_framework import viewsets
from datentool_backend.utils.views import (CanEditBasedataPermission,
                                           CanEditBasedata,
                                           HasAdminAccessOrReadOnly)

from .models import (SymbolForm, MapSymbol, LayerGroup, WMSLayer,
                     InternalWFSLayer, Source, AreaLevel, Area)
from .serializers import (SymbolFormSerializer, MapSymbolsSerializer,
                          LayerGroupSerializer, WMSLayerSerializer,
                          InternalWFSLayerSerializer, SourceSerializer,
                          AreaLevelSerializer, AreaSerializer)


class SymbolFormViewSet(viewsets.ModelViewSet):
    queryset = SymbolForm.objects.all()
    serializer_class = SymbolFormSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class MapSymbolsViewSet(viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolsSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class LayerGroupViewSet(viewsets.ModelViewSet):
    queryset = LayerGroup.objects.all()
    serializer_class = LayerGroupSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

class WMSLayerViewSet(viewsets.ModelViewSet):
    queryset = WMSLayer.objects.all()
    serializer_class = WMSLayerSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


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
