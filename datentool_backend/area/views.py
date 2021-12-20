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


class LayerGroupViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = LayerGroup.objects.all()
    serializer_class = LayerGroupSerializer


class WMSLayerViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = WMSLayer.objects.all()
    serializer_class = WMSLayerSerializer


class InternalWFSLayerViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = InternalWFSLayer.objects.all()
    serializer_class = InternalWFSLayerSerializer


class SourceViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer


class AreaLevelViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = AreaLevel.objects.all()
    serializer_class = AreaLevelSerializer


class AreaViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
