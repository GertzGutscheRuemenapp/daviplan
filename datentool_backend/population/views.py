from rest_framework import viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.decorators import action
# import for vector-tile functionality
#from django.views.generic import DetailView
#from vectortiles.mixins import BaseVectorTileView
#from django.views.generic import ListView
#from vectortiles.postgis.views import MVTView
from datentool_backend.utils.views import CanEditBasedataPermission
from .models import (Raster, PopulationRaster, Gender, AgeGroup, DisaggPopRaster,
                     Prognosis, PrognosisEntry, Population, PopulationEntry,
                     PopStatistic, PopStatEntry, RasterCell)
from .constants import RegStatAgeGroups, RegStatAgeGroup
from .serializers import (RasterSerializer, PopulationRasterSerializer,
                          GenderSerializer, AgeGroupSerializer,
                          DisaggPopRasterSerializer,PrognosisSerializer,
                          PrognosisEntrySerializer, PopulationSerializer,
                          PopulationEntrySerializer, PopStatisticSerializer,
                          PopStatEntrySerializer)


class RasterViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Raster.objects.all()
    serializer_class = RasterSerializer


class PopulationRasterViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = PopulationRaster.objects.all()
    serializer_class = PopulationRasterSerializer


#class RasterCellTileViewSet(MVTView, DetailView):
    #"""Due to Cellcode geometry, implementation of vector tiles"""
    #model = Raster
    #vector_tile_fields = ('name', )

    #def get_vector_tile_layer_name(self):
        #return self.get_object().name

    #def get_vector_tile_queryset(self):
        #return self.get_object().rastercell.all()

    #def get(self, request, *args, **kwargs):
        #self.object = self.get_object()
        #return BaseVectorTileView.get(self,request=request, z=kwargs.get('z'), x=kwargs.get('x'), y=kwargs.get('y'))


class GenderViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer


class AgeGroupViewSet(viewsets.ModelViewSet):
    queryset = AgeGroup.objects.all()
    serializer_class = AgeGroupSerializer

    def list(self, request, *args, **kwargs):
        # return the default age-groups (Regionalstatistik) when query parameter
        # ?defaults is set to true
        show_defaults = request.query_params.get('defaults')
        if show_defaults and show_defaults.lower() == 'true':
            res = [{'fromAge': a.from_age, 'toAge': a.to_age,
                    'code': a.code, 'label': a.name}
                   for a in RegStatAgeGroups.agegroups]
            return Response(res)
        return super().list(request, *args, **kwargs)

    @action(methods=['POST'], detail=False)
    def check(self, request, **kwargs):
        """
        route to compare posted age-groups with default age-groups
        (Regionalstatistik) in any order
        """
        try:
            age_groups = [RegStatAgeGroup(a['fromAge'], a['toAge'])
                          for a in request.data]
        except KeyError:
            raise ParseError()
        valid = RegStatAgeGroups.check(age_groups)
        return Response({'valid': valid})


class DisaggPopRasterViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = DisaggPopRaster.objects.all()
    serializer_class = DisaggPopRasterSerializer


class PrognosisViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Prognosis.objects.all()
    serializer_class = PrognosisSerializer


class PrognosisEntryViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = PrognosisEntry.objects.all()
    serializer_class = PrognosisEntrySerializer


class PopulationViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = Population.objects.all()
    serializer_class = PopulationSerializer


class PopulationEntryViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = PopulationEntry.objects.all()
    serializer_class = PopulationEntrySerializer


class PopStatisticViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = PopStatistic.objects.all()
    serializer_class = PopStatisticSerializer


class PopStatEntryViewSet(CanEditBasedataPermission, viewsets.ModelViewSet):
    queryset = PopStatEntry.objects.all()
    serializer_class = PopStatEntrySerializer
