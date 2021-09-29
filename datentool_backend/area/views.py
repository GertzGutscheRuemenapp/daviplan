from rest_framework import viewsets

from .models import SymbolForm, MapSymbol
from .serializers import SymbolFormSerializer, MapSymbolsSerializer


class SymbolFormViewSet(viewsets.ModelViewSet):
    queryset = SymbolForm.objects.all()
    serializer_class = SymbolFormSerializer


class MapSymbolsViewSet(viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolsSerializer
