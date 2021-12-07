from rest_framework import viewsets
from datentool_backend.utils.views import CanEditBasedataPermission

from .models import (SymbolForm, MapSymbol, LayerGroup, WMSLayer,
                     InternalWFSLayer, Source, AreaLevel, Area)
from .serializers import (SymbolFormSerializer, MapSymbolsSerializer,
                          LayerGroupSerializer, WMSLayerSerializer,
                          InternalWFSLayerSerializer, SourceSerializer,
                          AreaLevelSerializer, AreaSerializer)


class SymbolFormViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = SymbolForm.objects.all()
    serializer_class = SymbolFormSerializer


class MapSymbolsViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolsSerializer


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
