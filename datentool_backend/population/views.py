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

        # use only cells with population and put values from Census to column pop
        raster_cells = population.raster.popraster.raster.rastercell_set

        raster_cells_with_inhabitants = raster_cells\
            .filter(rastercellpopulation__isnull=False)\
            .annotate(pop=F('rastercellpopulation__value'),
                      )

        # spatial intersect with areas with inhabitants (entries in the PopualtionEntry)
        area_tbl = Area._meta.db_table
        popentry_tbl = PopulationEntry._meta.db_table

        rr = raster_cells_with_inhabitants.extra(
            select={f'area_id': f'"{area_tbl}".id',
                    f'm2_raster': 'st_area(st_transform(poly, 3035))',
                    f'm2_intersect': f'st_area(st_transform(st_intersection(poly, "{area_tbl}".geom), 3035))',
                    },
            tables=[area_tbl],
            where=[f'''st_intersects(poly, "{area_tbl}".geom)
            AND EXISTS (SELECT 1 FROM "{popentry_tbl}"
                        WHERE "{popentry_tbl}".area_id = "{area_tbl}".id
                        AND "{popentry_tbl}".population_id = %s
                        )
            '''],
            params=(population.id,),
        )

        df = pd.DataFrame.from_records(
            rr.values('id', 'area_id', 'pop', 'm2_raster', 'm2_intersect', 'cellcode'))\
            .set_index(['id', 'area_id'])

        # calculate weight as Census-Population *
        # share of area of the total area of the rastercell
        df['weight'] = df['pop'] * df['m2_intersect'] / df['m2_raster']

        # sum up the weights of all rastercells in an area
        area_weight = df['weight'].groupby(level='area_id').sum().rename('total_weight')

        # calculate the share of population, a rastercell
        # should get from the total population
        df = df.merge(area_weight, left_on='area_id', right_index=True)
        df['anteil_cell_of_area'] = df['weight'] / df['total_weight']

        # take the Area population by age_group and gender
        entries = population.populationentry_set
        df_pop = pd.DataFrame.from_records(
            entries.values('area_id', 'gender_id', 'age_group_id', 'value'))

        # left join with the shares of each rastercell
        dd = df_pop.merge(df.reset_index()[['id', 'area_id', 'anteil_cell_of_area']],
                          on='area_id',
                          how='left')\
            .set_index(['id', 'gender_id', 'age_group_id'])

        # areas without rastercells have no cell_id assigned
        cell_ids = dd.index.get_level_values('id')
        has_no_rastercell = pd.isna(cell_ids)
        population_not_located = dd.loc[has_no_rastercell].value.sum()

        if population_not_located:
            areas_without_rastercells = Area.objects.filter(
                id__in=dd.loc[has_no_rastercell, 'area_id'])
            msg = f'{population_not_located} Inhabitants not located to rastercells in {areas_without_rastercells}'
        else:
            msg = 'all areas have rastercells with inhabitants'

        # can work only when rastercells are found
        dd = dd.loc[~has_no_rastercell]


        # population by age_group and gender in each rastercell
        dd['pop'] = dd['value'] * dd['anteil_cell_of_area']

        # has to be summed up by rastercell, age_group and gender, because a rastercell
        # might have population from two areas
        df_cellagegender = dd['pop'].groupby(['id', 'gender_id', 'age_group_id']).sum()

        # delete the existing entries
        # updating would leave values for rastercells, that do not exist any more
        rc_exist = RasterCellPopulationAgeGender.objects\
            .filter(year=year.year, disaggraster=disaggraster)
        rc_exist.delete()

        # create RasterCellPopulationAgeGender-entries
        create_list = []
        # create an object for each row in df_cellagegender
        for (cell, gender, age_group), value in df_cellagegender.iteritems():
            entry = RasterCellPopulationAgeGender(
                disaggraster=disaggraster,
                year=year.year,
                cell_id=cell,
                gender_id=gender,
                age_group_id=age_group,
                value=value)

            create_list.append(entry)


        # update existing and create new objects
        RasterCellPopulationAgeGender.objects.bulk_create(create_list)
        msg = f'Disaggregation of Population on level {population.area_level} was successful. ' + msg
        return Response({'valid': 1, 'message': msg,})


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
