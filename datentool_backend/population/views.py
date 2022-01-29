import pandas as pd

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
                     RasterCellPopulationAgeGender,
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
        year = population.year
        disaggraster = population.raster
        entries = population.populationentry_set
        sq = population.populationentry_set.filter(area=OuterRef('pk'))
        areas_with_pop = Area.objects.annotate(has_p=Exists(sq)).filter(has_p=True)


        raster_cells = population.raster.popraster.raster.rastercell_set
        raster_fieldtype = raster_cells.model._meta.get_field('poly')

        raster_cells_with_inhabitants = raster_cells\
            .filter(rastercellpopulation__isnull=False)\
            .annotate(pop=F('rastercellpopulation__value'),
                      #m2_raster=ExpressionWrapper(A('poly'), output_field=FloatField()),
                      )

        rr = raster_cells_with_inhabitants.extra(
            select={'area_id': 'datentool_backend_area.id',
                    'm2_raster': 'st_area(st_transform(poly, 3035))',
                    'm2_intersect': 'st_area(st_transform(st_intersection(poly, datentool_backend_area.geom), 3035))',
                    },
            tables=['datentool_backend_area'],
            where=['st_intersects(poly, datentool_backend_area.geom)']
        )

        df = pd.DataFrame.from_records(
            rr.values('id', 'area_id', 'pop', 'm2_raster', 'm2_intersect', 'cellcode'))\
            .set_index(['id', 'area_id'])

        df['weight'] = df['pop'] * df['m2_intersect'] / df['m2_raster']

        area_weight = df['weight'].groupby(level='area_id').sum().rename('total_weight')

        df = df.merge(area_weight, left_on='area_id', right_index=True)
        df['anteil_cell_of_area'] = df['weight'] / df['total_weight']

        df_pop = pd.DataFrame.from_records(
            entries.values('area_id', 'gender_id', 'age_group_id', 'value'))

        dd = df_pop.merge(df.reset_index()[['id', 'area_id', 'anteil_cell_of_area']],
                          on='area_id')\
            .set_index(['id', 'gender_id', 'age_group_id'])
        dd['pop'] = dd['value'] * dd['anteil_cell_of_area']

        df_cellagegender = dd['pop'].groupby(['id', 'gender_id', 'age_group_id']).sum()

        create_list = []
        update_list = []
        rc_exist = RasterCellPopulationAgeGender.objects\
            .filter(year=year.year, disaggraster=disaggraster)\
            .values_list('id', 'cell_id', 'gender_id', 'age_group_id')

        rc_exist_dict = {rc[1:4]: rc[0] for rc in rc_exist}

        for (cell, gender, age_group), value in df_cellagegender.iteritems():
            rc_id = rc_exist_dict.get((cell, gender, age_group))
            entry = RasterCellPopulationAgeGender(
                id=rc_id,
                disaggraster=disaggraster,
                year=year.year,
                cell_id=cell,
                gender_id=gender,
                age_group_id=age_group,
                value=value)
            if rc_id is not None:
                update_list.append(entry)
            else:
                create_list.append(entry)
        RasterCellPopulationAgeGender.objects.bulk_create(create_list)
        RasterCellPopulationAgeGender.objects.bulk_update(update_list, fields=['value'])

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
