from rest_framework import viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.decorators import action
# import for vector-tile functionality
#from django.views.generic import DetailView
#from vectortiles.mixins import BaseVectorTileView
#from django.views.generic import ListView
#from vectortiles.postgis.views import MVTView
from datentool_backend.utils.views import (HasAdminAccess,
                                           CanEditBasedata,
                                           HasAdminAccessOrReadOnly)
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


class RasterViewSet(viewsets.ModelViewSet):
    queryset = Raster.objects.all()
    serializer_class = RasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationRasterViewSet(viewsets.ModelViewSet):
    queryset = PopulationRaster.objects.all()
    serializer_class = PopulationRasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


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


class GenderViewSet(viewsets.ModelViewSet):
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AgeGroupViewSet(viewsets.ModelViewSet):
    queryset = AgeGroup.objects.all()
    serializer_class = AgeGroupSerializer
    permission_classes = [HasAdminAccessOrReadOnly]

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
    def replace(self, request, **kwargs):
        AgeGroup.objects.all().delete()
        for a in request.data:
            g = AgeGroup(from_age=a['from_age'], to_age=a['to_age'])
            g.save()
        return self.list(request)

    @action(methods=['POST'], detail=False)
    def check(self, request, **kwargs):
        """
        route to compare posted age-groups with default age-groups
        (Regionalstatistik) in any order
        """
        try:
            age_groups = [RegStatAgeGroup(a, a['toAge'])
                          for a in request.data]
        except KeyError:
            raise ParseError()
        valid = RegStatAgeGroups.check(age_groups)
        return Response({'valid': valid})


class DisaggPopRasterViewSet(viewsets.ModelViewSet):
    queryset = DisaggPopRaster.objects.all()
    serializer_class = DisaggPopRasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PrognosisViewSet(viewsets.ModelViewSet):
    queryset = Prognosis.objects.all()
    serializer_class = PrognosisSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PrognosisEntryViewSet(viewsets.ModelViewSet):
    queryset = PrognosisEntry.objects.all()
    serializer_class = PrognosisEntrySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationViewSet(viewsets.ModelViewSet):
    queryset = Population.objects.all()
    serializer_class = PopulationSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationEntryViewSet(viewsets.ModelViewSet):
    queryset = PopulationEntry.objects.all()
    serializer_class = PopulationEntrySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopStatisticViewSet(viewsets.ModelViewSet):
    queryset = PopStatistic.objects.all()
    serializer_class = PopStatisticSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopStatEntryViewSet(viewsets.ModelViewSet):
    queryset = PopStatEntry.objects.all()
    serializer_class = PopStatEntrySerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
