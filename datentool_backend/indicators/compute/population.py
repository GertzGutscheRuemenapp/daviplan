from typing import Dict

from django.db import connection
from django.db.models import Count
from django.core.exceptions import BadRequest
from django.http.request import QueryDict

from datentool_backend.utils.dict_cursor import dictfetchall

from datentool_backend.indicators.compute.base import ComputeIndicator, ResultSerializer
from datentool_backend.area.models import Area
from datentool_backend.population.models import (RasterCellPopulationAgeGender,
                                                 AreaCell,
                                                 RasterCellPopulation,
                                                 AreaPopulationAgeGender,
                                                 PopulationAreaLevel,
                                                 Population,
                                                 )
from datentool_backend.user.models.process import Scenario


class PopulationIndicatorMixin:

    def get_rasterpop(self) -> RasterCellPopulationAgeGender:
        """get the population per rastercell in the scenario"""
        filter_params = self.get_filter_params()

        # filter the rastercell-population by year, age_group and gender, if given
        rasterpop = RasterCellPopulationAgeGender.objects.filter(**filter_params)
        return rasterpop

    def get_areapop(self, filter_params: Dict[str, int] = {}) -> AreaPopulationAgeGender:
        """get the population per area in the scenario"""
        filter_params.update(self.get_filter_params())

        # filter the area-population by year, age_group and gender, if given
        areapop = AreaPopulationAgeGender.objects.filter(**filter_params)
        return areapop

    def get_populations(self) -> Population:
        """get the population"""
        filter_params = self.get_population_filter_params()
        population = Population.objects.filter(**filter_params)
        return population

    def get_filter_params(self) -> Dict[str, int]:
        """get the filter params for """
        scenario = self.data.get('scenario')
        if scenario:
            prognosis = Scenario.objects.get(pk=scenario).prognosis_id
        else:
            prognosis = self.data.get('prognosis') or None
        filter_params = {'population__prognosis': prognosis, }
        year = self.data.get('year')
        if year:
            filter_params['population__year__year'] = year

        if isinstance(self.data, QueryDict):
            genders = self.data.getlist('gender')
            age_groups = self.data.getlist('age_group')
        else:
            genders = self.data.get('gender')
            age_groups = self.data.get('age_group')

        if genders and genders != ['']:
            filter_params['gender__in'] = genders
        if age_groups and age_groups != ['']:
            filter_params['age_group__in'] = age_groups
        return filter_params

    def get_population_filter_params(self) -> Dict[str, int]:
        scenario = self.data.get('scenario')
        if scenario:
            prognosis = Scenario.objects.get(pk=scenario).prognosis_id
        else:
            prognosis = self.data.get('prognosis') or None
        filter_params = {'prognosis': prognosis, }
        year = self.data.get('year')
        if year:
            filter_params['year__year'] = year
        return filter_params

    def get_areas(self, area_level_id: int = None) -> Area:
        """get the relevant areas"""
        # filter areas
        area_filter = {}
        if isinstance(self.data, QueryDict):
            areas = self.data.getlist('area')
        else:
            areas = self.data.get('area')
        if areas and areas != ['']:
            area_filter['id__in'] = areas

        if area_level_id is None:
            levels = Area.objects.filter(**area_filter).values_list(
                'area_level_id', flat=True).distinct()
            if len(levels) > 1:
                raise Exception('Areas have to be of the same level')
            area_level_id = levels[0]

        areas = Area.label_annotated_qs(area_level=area_level_id)\
            .filter(**area_filter)
        return areas


class ComputePopulationAreaIndicator(PopulationIndicatorMixin,
                                     ComputeIndicator):
    title = 'Population By Area'
    description = 'Total Population per Area'
    result_serializer = ResultSerializer.AREA

    def compute(self):
        """"""
        area_level_id = self.data.get('area_level')
        if area_level_id is None:
            raise BadRequest('No AreaLevel provided')
        areas = self.get_areas(area_level_id=area_level_id)

        q_areas, p_areas = areas.values('id', '_label').query.sql_with_params()

        populations = self.get_populations()
        if not populations:
            return []
        population = populations[0]

        pop_arealevel, created = PopulationAreaLevel.objects.get_or_create(
            population=population,
            area_level_id=area_level_id)

        #  check if the area-population is precalculated
        if pop_arealevel.up_to_date:
            areapop = self.get_areapop(
                filter_params={'area__area_level_id': area_level_id, })

            q_areapop, p_areapop = areapop.values('area_id', 'value')\
                .query.sql_with_params()

            query = f'''SELECT
            a."id", a."_label", val."value"
            FROM ({q_areas}) AS a
            LEFT JOIN (
              SELECT
                ap."area_id",
                SUM(ap."value") AS "value"
              FROM
                ({q_areapop}) AS ap
              GROUP BY ap."area_id"
            ) val ON (val."area_id" = a."id")
            '''

            params = p_areas + p_areapop

        else:
            # calculate it from the raster cells
            rcp = RasterCellPopulation.objects.all()
            acells = AreaCell.objects.filter(area__area_level_id=area_level_id)
            rasterpop = self.get_rasterpop()

            # sum up the rastercell-population to areas
            # taking the share_area_of_cell into account
            q_acells, p_acells = acells.values(
                'area_id', 'cell_id', 'share_area_of_cell').query.sql_with_params()
            q_pop, p_pop = rasterpop.values('cell_id', 'value').query.sql_with_params()
            q_rcp, p_rcp = rcp.values('id', 'cell_id').query.sql_with_params()

            query = f'''SELECT
            a."id", a."_label", val."value"
            FROM ({q_areas}) AS a
            LEFT JOIN (
              SELECT
                ac."area_id",
                SUM(p."value" * ac."share_area_of_cell") AS "value"
              FROM
                ({q_acells}) AS ac,
                ({q_pop}) AS p,
                ({q_rcp}) AS rcp
              WHERE ac."cell_id" = rcp."id"
                AND p."cell_id" = rcp."cell_id"
              GROUP BY ac."area_id"
            ) val ON (val."area_id" = a."id")
            '''

            params = p_areas + p_acells + p_pop + p_rcp

        areas_with_pop = Area.objects.raw(query, params)

        return areas_with_pop


class ComputePopulationDetailIndicator(PopulationIndicatorMixin,
                                       ComputeIndicator):
    title = 'Population By Gender, AgeGroup and Year'
    description = 'Population by Gender, Agegroup and Year for one or several areas'
    result_serializer = ResultSerializer.POP

    def compute(self):
        """"""
        areas = self.get_areas()
        area_levels = areas.values('area_level_id').annotate(cnt=Count('pk'))
        populations = self.get_populations()

        up_to_date = True
        for population in populations:
            #  check if the area-population is precalculated for all area_levels
            for area_level in area_levels:
                pop_arealevel, created = PopulationAreaLevel.objects.get_or_create(
                    population=population,
                    area_level_id=area_level['area_level_id'])
                if not pop_arealevel.up_to_date:
                    up_to_date = False
                    break

        if up_to_date:
            areapop = self.get_areapop(
                filter_params={'area_id__in': areas, })

            q_areapop, p_areapop = areapop.values(
                'area_id', 'age_group_id', 'gender_id', 'value',
                'population__year__year')\
                .query.sql_with_params()

            query = f'''SELECT
              ap."year" AS "year",
              ap."age_group_id" AS agegroup,
              ap."gender_id" AS gender,
              SUM(ap."value") AS "value"
            FROM
              ({q_areapop}) AS ap
            GROUP BY ap."year", ap."age_group_id", ap."gender_id"
            '''

            params = p_areapop

        else:
            # calculate the values from the rastercells
            rcp = RasterCellPopulation.objects.all()
            acells = AreaCell.objects.filter(area__in=areas)
            # filter the rastercell-population by year, age_group and gender, if given
            rasterpop = self.get_rasterpop()

            # sum up the rastercell-population by year, age_group, and gender

            q_acells, p_acells = acells.values(
                'area_id', 'cell_id', 'share_area_of_cell').query.sql_with_params()
            q_pop, p_pop = rasterpop.values(
                'id', 'cell_id', 'value', 'age_group_id', 'gender_id',
                'population__year__year')\
                .query.sql_with_params()
            q_rcp, p_rcp = rcp.values(
                'id', 'cell_id').query.sql_with_params()

            query = f'''SELECT
              p."year",
              p."age_group_id" AS agegroup,
              p."gender_id" AS gender,
              SUM(p."value" * ac."share_area_of_cell") AS "value"
            FROM
              ({q_acells}) AS ac,
              ({q_pop}) AS p,
              ({q_rcp}) AS rcp
            WHERE ac."cell_id" = rcp."id"
            AND p."cell_id" = rcp."cell_id"
            GROUP BY p."year", p."age_group_id", p."gender_id"
            '''

            params = p_acells + p_pop + p_rcp

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            qs = dictfetchall(cursor)

        return qs

