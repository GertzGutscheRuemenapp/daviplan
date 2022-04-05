import pandas as pd
from io import StringIO
from django.db import connection
from typing import List
from django.db.models import F

from datentool_backend.models import (Area, PopulationRaster, AreaCell,
                                      AreaLevel, Population,
                                      PopulationAreaLevel,
                                      AreaPopulationAgeGender,
                                      RasterCellPopulationAgeGender,
                                      RasterCellPopulation)

def intersect_areas_with_raster(
    areas: List[Area], pop_raster: PopulationRaster=None,
    drop_constraints: bool=False):
    '''
    intersect areas with raster creating AreaCells in database,
    already existing AreaCells for areas in this raster are dropped
    '''

    if not pop_raster:
        pop_raster = PopulationRaster.objects.first()
    if not pop_raster:
        return

    # use only cells with population and put values from Census to column pop
    raster_cells = pop_raster.raster.rastercell_set

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
        params=(tuple(areas.values_list('id', flat=True)),),
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

    df2 = df[['rcp_id', 'share_area_of_cell', 'share_cell_of_area']]\
        .reset_index()\
        .rename(columns={'rcp_id': 'cell_id'})[['area_id', 'cell_id', 'share_area_of_cell', 'share_cell_of_area']]

    ac = AreaCell.objects.filter(area__in=areas, cell__popraster=pop_raster)
    ac.delete()

    with StringIO() as file:
        df2.to_csv(file, index=False)
        file.seek(0)
        AreaCell.copymanager.from_csv(file,
            drop_constraints=drop_constraints, drop_indexes=drop_constraints)

def aggregate_population(area_level: AreaLevel, population: Population,
                         drop_constraints=False):
    acells = AreaCell.objects.filter(area__area_level=area_level)

    rasterpop = RasterCellPopulationAgeGender.objects.filter(population=population)
    rcp = RasterCellPopulation.objects.all()

    q_acells, p_acells = acells.values(
        'area_id', 'cell_id', 'share_area_of_cell').query.sql_with_params()
    q_pop, p_pop = rasterpop.values(
        'population_id', 'cell_id', 'value', 'age_group_id', 'gender_id')\
        .query.sql_with_params()
    q_rcp, p_rcp = rcp.values(
        'id', 'cell_id').query.sql_with_params()

    query = f'''SELECT
      p."population_id",
      ac."area_id",
      p."age_group_id",
      p."gender_id",
      SUM(p."value" * ac."share_area_of_cell") AS "value"
    FROM
      ({q_acells}) AS ac,
      ({q_pop}) AS p,
      ({q_rcp}) AS rcp
    WHERE ac."cell_id" = rcp."id"
    AND p."cell_id" = rcp."cell_id"
    GROUP BY p."population_id", ac."area_id", p."age_group_id", p."gender_id"
    '''

    params = p_acells + p_pop + p_rcp

    columns = ['population_id', 'area_id', 'age_group_id', 'gender_id', 'value']

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    df_areaagegender = pd.DataFrame(rows, columns=columns)

    ap_exist = AreaPopulationAgeGender.objects\
        .filter(population=population, area__area_level=area_level)
    ap_exist.delete()

    with StringIO() as file:
        df_areaagegender.to_csv(file, index=False)
        file.seek(0)
        AreaPopulationAgeGender.copymanager.from_csv(
            file,
            drop_constraints=drop_constraints, drop_indexes=drop_constraints,
        )

    # validate_cache
    pop_arealevel, created = PopulationAreaLevel.objects.get_or_create(
        population=population,
        area_level=area_level)
    pop_arealevel.up_to_date = True
    pop_arealevel.save()
