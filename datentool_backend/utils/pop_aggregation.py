from typing import List


import pandas as pd
import numpy as np
from django.db import connection, transaction
from django.db.utils import ProgrammingError
from django.db.models import Max, Sum, F
from django.conf import settings

from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.population.models import (
    PopulationRaster,
    AreaCell,
    Population,
    PopulationAreaLevel,
    AreaPopulationAgeGender,
    RasterCellPopulationAgeGender,
    RasterCellPopulation)
from datentool_backend.utils.raw_delete import delete_chunks
from datentool_backend.utils.excel_template import write_template_df

import logging
logger = logging.getLogger('population')


def disaggregate_population(population: Population,
                            use_intersected_data: bool=False,
                            drop_constraints: bool=False):
    areas = population.populationentry_set.distinct('area_id')\
        .values_list('area_id', flat=True)
    if not areas:
        return 'skipped'

    popraster = population.popraster or PopulationRaster.objects.first()

    ac = AreaCell.objects.filter(area__in=areas,
                                 rastercellpop__popraster=popraster)

    # if rastercells are not intersected yet
    if ac and use_intersected_data:
        msg = 'use precalculated rastercells\n'
    else:
        intersect_areas_with_raster(Area.objects.filter(id__in=areas),
                                    pop_raster=population.popraster)
        msg = f'{len(areas)} Areas intersected with Rastercells.\n'
        ac = AreaCell.objects.filter(area__in=areas,
                                     rastercellpop__popraster=population.popraster)
    if not ac:
        return 'no area cells found to intersect with'

    # get the intersected data from the database
    df_area_cells = pd.DataFrame.from_records(
        ac.values('rastercellpop__cell_id', 'area_id', 'share_cell_of_area'))\
        .rename(columns={'rastercellpop__cell_id': 'cell_id', })

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
        area_levels = population.populationentry_set\
            .distinct('area__area_level_id')\
            .values('area__area_level')
        area_level = area_levels[0]['area__area_level']

        areas_without_rastercells = Area\
            .label_annotated_qs(area_level)\
            .filter(id__in=dd.loc[has_no_rastercell, 'area_id'])\
            .values_list('_label', flat=True)

        msg += f'{population_not_located} Inhabitants not located '\
        f'to rastercells in {list(areas_without_rastercells)}\n'
    else:
        msg += 'all areas have rastercells with inhabitants\n'

    # can work only when rastercells are found
    dd = dd.loc[~has_no_rastercell]

    # population by age_group and gender in each rastercell
    dd.loc[:, 'pop'] = dd['value'] * dd['share_cell_of_area']

    # has to be summed up by rastercell, age_group and gender, because a rastercell
    # might have population from two areas
    df_cellagegender: pd.DataFrame = dd['pop']\
        .groupby(['cell_id', 'gender_id', 'age_group_id'])\
        .sum()\
        .rename('value')\
        .reset_index()

    df_cellagegender['cell_id'] = df_cellagegender['cell_id'].astype('i8')
    df_cellagegender['population_id'] = population.id

    # delete the existing entries
    # updating would leave values for rastercells, that do not exist any more
    rc_exist = RasterCellPopulationAgeGender.objects\
        .filter(population=population)
    delete_chunks(rc_exist, logger)

    model = RasterCellPopulationAgeGender
    model_name = model._meta.object_name
    n_rows = len(df_cellagegender)
    logger.info(f'Schreibe {n_rows:n} Einträge')
    stepsize = settings.STEPSIZE
    for i in np.arange(0, n_rows, stepsize, dtype=np.int64):
        chunk = df_cellagegender.iloc[i:i + stepsize]
        n_inserted = len(chunk)
        write_template_df(chunk, model, logger,
                          drop_constraints=drop_constraints,
                          log_level=logging.DEBUG)
        logger.debug(f'{i + n_inserted:n}/{n_rows:n} {model_name}-Einträgen geschrieben')

    return msg


def intersect_areas_with_raster(
    areas: List[Area],
    pop_raster: PopulationRaster=None,
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

    # ToDo: do intersection first to check number of areas that intersect with
    # raster, causes error if no area intersects with raster
    try:
        if not rr:
            return
    except ProgrammingError:
        return

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
        .rename(columns={'rcp_id': 'rastercellpop_id'})[
            ['area_id', 'rastercellpop_id', 'share_area_of_cell', 'share_cell_of_area']]

    ac = AreaCell.objects.filter(area__in=areas, rastercellpop__popraster=pop_raster)
    delete_chunks(ac, logger)

    model = AreaCell
    model_name = model._meta.object_name
    n_rows = len(df2)
    logger.info(f'Schreibe insgesamt {n_rows:n} Einträge')
    stepsize = settings.STEPSIZE
    for i in np.arange(0, n_rows, stepsize, dtype=np.int64):
        chunk = df2.iloc[i:i + stepsize]
        n_inserted = len(chunk)
        write_template_df(chunk, model, logger,
                          drop_constraints=drop_constraints,
                          log_level=logging.DEBUG)
        logger.debug(f'{i + n_inserted:n}/{n_rows:n} {model_name}-Einträgen geschrieben')


def aggregate_many(area_levels, populations, drop_constraints=False):

    manager = AreaPopulationAgeGender.copymanager
    with transaction.atomic():
        if drop_constraints:
            manager.drop_constraints()
            manager.drop_indexes()

        for i, area_level in enumerate(area_levels):
            for population in populations:
                aggregate_population(area_level, population,
                                     drop_constraints=False)
            entries = AreaPopulationAgeGender.objects.filter(
                area__area_level=area_level)
            summed_values = entries.values(
                'population__year', 'area', 'population__prognosis')\
                .annotate(Sum('value'))
            max_value = summed_values.aggregate(
                Max('value__sum'))['value__sum__max']
            area_level.max_population = max_value
            area_level.population_cache_dirty = False
            area_level.save()
            logger.info(f'Daten auf Gebietseinheit {area_level.name} aggregiert '
                        f'{i + 1}/{len(area_levels)}')

        if drop_constraints:
            manager.restore_constraints()
            manager.restore_indexes()


def aggregate_population(area_level: AreaLevel, population: Population,
                         drop_constraints=False):
    acells = AreaCell.objects.filter(area__area_level=area_level)

    rasterpop = RasterCellPopulationAgeGender.objects.filter(population=population)
    rcp = RasterCellPopulation.objects.all()

    q_acells, p_acells = acells.values(
        'area_id', 'rastercellpop_id', 'share_area_of_cell').query.sql_with_params()
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
    WHERE ac."rastercellpop_id" = rcp."id"
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
    delete_chunks(ap_exist, logger)

    model = AreaPopulationAgeGender
    model_name = model._meta.object_name
    n_rows = len(df_areaagegender)
    logger.info(f'Schreibe insgesamt {n_rows:n} Einträge')
    stepsize = settings.STEPSIZE
    for i in np.arange(0, n_rows, stepsize, dtype=np.int64):
        chunk = df_areaagegender.iloc[i:i + stepsize]
        n_inserted = len(chunk)
        write_template_df(chunk, model, logger,
                          drop_constraints=drop_constraints,
                          log_level=logging.DEBUG)
        logger.debug(f'{i + n_inserted:n}/{n_rows:n} {model_name}-Einträgen geschrieben')

    # validate_cache
    pop_arealevel, created = PopulationAreaLevel.objects.get_or_create(
        population=population,
        area_level=area_level)
    pop_arealevel.up_to_date = True
    pop_arealevel.save()
