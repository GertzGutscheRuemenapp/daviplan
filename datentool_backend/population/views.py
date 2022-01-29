from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.db.models.functions import Area as A, Intersection
from django.db.models import OuterRef, Subquery, Count, IntegerField, FloatField, Sum
from django.db.models import Q, F, Exists, ExpressionWrapper
from django.contrib.gis.db.models import PolygonField
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .models import (Raster,
                     PopulationRaster,
                     DisaggPopRaster,
                     Prognosis,
                     PrognosisEntry,
                     Population,
                     PopulationEntry,
                     PopStatistic,
                     PopStatEntry,
                     RasterCell,
                     RasterCellPopulation,
                     )
from .serializers import (RasterSerializer,
                          PopulationRasterSerializer,
                          DisaggPopRasterSerializer,
                          PrognosisSerializer,
                          PrognosisEntrySerializer,
                          PopulationSerializer,
                          PopulationEntrySerializer,
                          PopStatisticSerializer,
                          PopStatEntrySerializer,
                          )

from datentool_backend.area.models import Area

class RasterViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Raster.objects.all()
    serializer_class = RasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationRasterViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PopulationRaster.objects.all()
    serializer_class = PopulationRasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class DisaggPopRasterViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = DisaggPopRaster.objects.all()
    serializer_class = DisaggPopRasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PrognosisViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
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

    @action(methods=['GET'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def disaggregate(self, request, **kwargs):
        """
        route to disaggregate the population to the raster cells
        """
        population = self.queryset[0]
        entries = population.populationentry_set
        sq = population.populationentry_set.filter(area=OuterRef('pk'))
        areas_with_pop = Area.objects.annotate(has_p=Exists(sq)).filter(has_p=True)


        raster_cells = population.raster.popraster.raster.rastercell_set
        raster_fieldtype = raster_cells.model._meta.get_field('poly')

        raster_cells_with_inhabitants = raster_cells\
            .filter(rastercellpopulation__isnull=False)\
            .annotate(pop=F('rastercellpopulation__value'))
        # verschneide die verschiedenen areas mit den rastercells
        sq = raster_cells_with_inhabitants.filter(poly__intersects=OuterRef('geom'))
        sq = sq.annotate(m2_raster=ExpressionWrapper(A('poly'), output_field=FloatField()))
        sq = sq.annotate(m2_inter=ExpressionWrapper(A(
            ExpressionWrapper(Intersection(
                ExpressionWrapper(OuterRef('geom'), output_field=raster_fieldtype),
                'poly')
            , output_field=raster_fieldtype)), output_field=FloatField()))
        sq = sq.annotate(weight=F('pop')*F('m2_inter')/F('m2_raster'))
        sq = sq.annotate(area_id=OuterRef('pk'))
        group = sq.values('area_id')
        sq_g = group.annotate(n_cells=Count('*'),
                                    m2=Sum('m2_inter'),
                                    weight=Sum('weight'),
                                    )

        a = areas_with_pop.annotate(n_rastercells=Subquery(sq_g.values('n_cells')),
                                    m2=Subquery(sq_g.values('m2')),
                                    weight=Subquery(sq_g.values('weight')))


        # annotate
        # m2=
        # (weight_raster=Area(Intersection(a.geom, e.poly))/Area(e.poly)*raster__einwohner
        # cell,area,weight_raster
        # total_weight=Sum(weight_raster) GROUP BY area
        # area,total_weight
        #
        # joine entry mit rastercell
        # area,agegroup,gender,cell,value*weight_raster/total_weight AS value

        # cell,agegroup,gender, sum(total_weight) AS value GROUP BY cell,agegroup,gender
        # get_or_create RasterCellPopulationAgeGender(cell,agegroup,gender)
        # bulk_update values
        entries.values('area').filter()
        entries_with_area = entries\
            .filter(Q(area__geom__intersects=OuterRef('poly'))
                    & Q())\
            .annotate(cell_id=OuterRef('id'))\
            .values('cell_id', 'age_group_id', 'gender_id')

        entries_with_pop = entries_with_area\
            .annotate(sum_pop=Sum('value'))\
            .values('sum_pop')
        raster_cells_with_pop = raster_cells.annotate(
            area_pop=Subquery(entries_with_pop, output_field=FloatField())
        )

        import pandas as pd
        df = pd.DataFrame.from_records(population.populationentry_set.values(
            'area_id', 'gender_id', 'age_group_id', 'value',
        ))
        da = df.to_xarray()
        return Response({'valid': 1})



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
