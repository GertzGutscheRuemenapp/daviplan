from rest_framework import viewsets

from .models import (Year, Raster, PopulationRaster, RasterCell)
from .serializers import (YearSerializer, RasterSerializer,
                          PopulationRasterSerializer, RasterCellSerializer)


class YearViewSet(viewsets.ModelViewSet):
    queryset = Year.objects.all()
    serializer_class = YearSerializer


class RasterViewSet(viewsets.ModelViewSet):
    queryset = Raster.objects.all()
    serializer_class = RasterSerializer


class PopulationRasterViewSet(viewsets.ModelViewSet):
    queryset = PopulationRaster.objects.all()
    serializer_class = PopulationRasterSerializer


class RasterCellViewSet(viewsets.ModelViewSet):
    queryset = RasterCell.objects.all()
    serializer_class = RasterCellSerializer