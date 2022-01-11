from rest_framework import viewsets
from datentool_backend.utils.views import (CanEditBasedata,
                                           HasAdminAccessOrReadOnly,
                                           ProtectCascadeMixin)

from .models import (MapSymbol, LayerGroup, WMSLayer,
                     InternalWFSLayer, Source, AreaLevel, Area)
from .serializers import (MapSymbolsSerializer,
                          LayerGroupSerializer, WMSLayerSerializer,
                          InternalWFSLayerSerializer, SourceSerializer,
                          AreaLevelSerializer, AreaSerializer)


class MapSymbolsViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolsSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class LayerGroupViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = LayerGroup.objects.all()
    serializer_class = LayerGroupSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class WMSLayerViewSet(viewsets.ModelViewSet):
    queryset = WMSLayer.objects.all()
    serializer_class = WMSLayerSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


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
