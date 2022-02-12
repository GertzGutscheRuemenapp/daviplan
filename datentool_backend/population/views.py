import pandas as pd

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import F

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
#from datentool_backend.indicators.compute import (IntersectAreaWithRaster,
                                                  #DisaggregatePopulation)

from .models import (Raster,
                     PopulationRaster,
                     Prognosis,
                     Population,
                     PopulationEntry,
                     PopStatistic,
                     PopStatEntry,
                     RasterCellPopulationAgeGender,
                     AreaCell,
                     )
from .serializers import (RasterSerializer,
                          PopulationRasterSerializer,
                          PrognosisSerializer,
                          PopulationSerializer,
                          PopulationEntrySerializer,
                          PopStatisticSerializer,
                          PopStatEntrySerializer,
                          MessageSerializer,
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


class PrognosisViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Prognosis.objects.all()
    serializer_class = PrognosisSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationViewSet(viewsets.ModelViewSet):
    queryset = Population.objects.all()
    serializer_class = PopulationSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


    @extend_schema(description='intersect areas with rastercells',
                   parameters=[
                       OpenApiParameter(name='area_level', required=False, type=int,
        description='''if a specific area_level_id is provided,
        take this one instead of the areas of the population''')
                   ],
                   responses={202: OpenApiResponse(MessageSerializer, 'Intersection successful'),
                              406: OpenApiResponse(MessageSerializer, 'Intersection failed')})
    @action(methods=['GET'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def intersectareaswithcells(self, request, **kwargs):
        """
        route to intersect areas with raster cells
        """
        population: Population = self.queryset.get(**self.kwargs)

        # if a specific area-level is provided, take this one
        # instead of the areas of the population
        area_level_id = request.query_params.get('area_level')
        if area_level_id:
            areas = Area.objects.filter(area_level_id=area_level_id)\
                .values_list('pk', flat=True)
        else:
            areas = population.populationentry_set.distinct('area_id')\
                .values_list('area_id', flat=True)

        # use only cells with population and put values from Census to column pop
        raster_cells = population.popraster.raster.rastercell_set

        raster_cells_with_inhabitants = raster_cells\
            .filter(rastercellpopulation__isnull=False)\
            .annotate(pop=F('rastercellpopulation__value'),
                      rcp_id=F('rastercellpopulation__id'),
                      )

        # spatial intersect with areas from given area_level
        area_tbl = Area._meta.db_table

        rr = raster_cells_with_inhabitants.extra(
            select={f'area_id': f'"{area_tbl}".id',
                    f'm2_raster': 'st_area(st_transform(poly, 3035))',
                    f'm2_intersect': f'st_area(st_transform(st_intersection(poly, "{area_tbl}".geom), 3035))',
                    },
            tables=[area_tbl],
            where=[f'''st_intersects(poly, "{area_tbl}".geom)
            AND "{area_tbl}".id IN %s
            '''],
            params=(tuple(areas),),
        )

        df = pd.DataFrame.from_records(
            rr.values('id', 'area_id', 'pop', 'rcp_id',
                      'm2_raster', 'm2_intersect', 'cellcode'))\
            .set_index(['id', 'area_id'])

        df['share_area_of_cell'] = df['m2_intersect'] / df['m2_raster']

        # calculate weight as Census-Population *
        # share of area of the total area of the rastercell
        df['weight'] = df['pop'] * df['m2_intersect'] / df['m2_raster']

        # sum up the weights of all rastercells in an area
        area_weight = df['weight'].groupby(level='area_id').sum().rename('total_weight')

        # calculate the share of population, a rastercell
        # should get from the total population
        df = df.merge(area_weight, left_on='area_id', right_index=True)
        df['share_cell_of_area'] = df['weight'] / df['total_weight']

        # sum up the weights of all areas in a cell
        cell_weight = df['weight'].groupby(level='id').sum().rename('total_weight_cell')

        df = df.merge(cell_weight, left_on='id', right_index=True)
        df['share_area_of_cell'] = df['weight'] / df['total_weight_cell']


        ac = AreaCell.objects.filter(area__in=areas,
                                     cell__popraster=population.popraster)
        ac.delete()

        # create AreaCell-entries
        create_list = []
        # create an object for each row in df
        for (cell_id, area_id), row in df[['rcp_id', 'share_area_of_cell', 'share_cell_of_area']].iterrows():
            rcp_id, share_area_of_cell, share_cell_of_area = row

            entry = AreaCell(
                area_id=area_id,
                cell_id=rcp_id,
                share_area_of_cell=share_area_of_cell,
                share_cell_of_area=share_cell_of_area,
            )
            create_list.append(entry)
        AreaCell.objects.bulk_create(create_list)
        msg = f'{len(areas)} Areas were successfully intersected with Rastercells.\n'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(description='intersect areas with rastercells',
                   parameters=[
                       OpenApiParameter(name='area_level', required=False, type=int,
        description='''if a specific area_level_id is provided,
        take this one instead of the areas of the population'''),
                       OpenApiParameter(name='use_intersected_data', required=False, type=bool,
        description='''use precalculated rastercells''')

                   ],
                   responses={202: OpenApiResponse(MessageSerializer, 'Intersection successful'),
                              406: OpenApiResponse(MessageSerializer, 'Intersection failed')})
    @action(methods=['GET'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def disaggregate(self, request, **kwargs):
        """
        route to disaggregate the population to the raster cells
        """
        population: Population = self.queryset.get(**self.kwargs)
        areas = population.populationentry_set.distinct('area_id')\
            .values_list('area_id', flat=True)

        ac = AreaCell.objects.filter(area__in=areas,
                                     cell__popraster=population.popraster)

        # if rastercells are not intersected yet
        if ac and request.query_params.get('use_intersected_data'):
            msg = 'use precalculated rastercells\n'
        else:
            response = self.intersectareaswithcells(request)
            msg = response.data.get('message', '')
            ac = AreaCell.objects.filter(area__in=areas,
                                         cell__popraster=population.popraster)

        # get the intersected data from the database
        df_area_cells = pd.DataFrame.from_records(
            ac.values('cell__cell_id', 'area_id', 'share_cell_of_area'))\
            .rename(columns={'cell__cell_id': 'cell_id',})

        # take the Area population by age_group and gender
        entries = population.populationentry_set
        df_pop = pd.DataFrame.from_records(
            entries.values('area_id', 'gender_id', 'age_group_id', 'value'))

        # left join with the shares of each rastercell
        dd = df_pop.merge(df_area_cells,
                          on='area_id',
                          how='left')\
            .set_index(['cell_id', 'gender_id', 'age_group_id'])

        # areas without rastercells have no cell_id assigned
        cell_ids = dd.index.get_level_values('cell_id')
        has_no_rastercell = pd.isna(cell_ids)
        population_not_located = dd.loc[has_no_rastercell].value.sum()

        if population_not_located:
            areas_without_rastercells = Area.objects.filter(
                id__in=dd.loc[has_no_rastercell, 'area_id'])
            msg += f'{population_not_located} Inhabitants not located to rastercells in {areas_without_rastercells}\n'
        else:
            msg += 'all areas have rastercells with inhabitants\n'

        # can work only when rastercells are found
        dd = dd.loc[~has_no_rastercell]

        # population by age_group and gender in each rastercell
        dd['pop'] = dd['value'] * dd['share_cell_of_area']

        # has to be summed up by rastercell, age_group and gender, because a rastercell
        # might have population from two areas
        df_cellagegender = dd['pop'].groupby(['cell_id', 'gender_id', 'age_group_id']).sum()

        # delete the existing entries
        # updating would leave values for rastercells, that do not exist any more
        rc_exist = RasterCellPopulationAgeGender.objects\
            .filter(population=population)
        rc_exist.delete()

        # create RasterCellPopulationAgeGender-entries
        create_list = []
        # create an object for each row in df_cellagegender
        for (cell, gender, age_group), value in df_cellagegender.iteritems():
            entry = RasterCellPopulationAgeGender(
                population=population,
                cell_id=cell,
                gender_id=gender,
                age_group_id=age_group,
                value=value)

            create_list.append(entry)

        # update existing and create new objects
        RasterCellPopulationAgeGender.objects.bulk_create(create_list)
        msg += f'Disaggregation of Population was successful.\n'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


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
