from typing import Tuple, List
from django.core.exceptions import BadRequest

from datentool_backend.population.models import AreaCell, RasterCellPopulation
from datentool_backend.indicators.compute.base import ComputeIndicator, ResultSerializer
from datentool_backend.indicators.compute.population import PopulationIndicatorMixin
from datentool_backend.area.models import Area
from datentool_backend.population.models import PopulationAreaLevel


class DemandAreaIndicator(PopulationIndicatorMixin,
                          ComputeIndicator):
    label = 'Demand for Service By Area'
    description = 'Total Demand for Service per Area'
    result_serializer = ResultSerializer.AREA

    def get_query_and_params(self) -> Tuple[str, List[str]]:
        """get the query and the params for the indicator"""

        scenario_id = self.data.get('scenario')
        service_id = self.data.get('service')

        area_level_id = self.data.get('area_level')
        if area_level_id is None:
            raise BadRequest('No AreaLevel provided')
        areas = self.get_areas(area_level_id=area_level_id)

        q_areas, p_areas = areas.values('id', '_label').query.sql_with_params()

        populations = self.get_populations()
        if not populations:
            return None, None
        population = populations[0]

        pop_arealevel, created = PopulationAreaLevel.objects.get_or_create(
            population=population,
            area_level_id=area_level_id)

        demand_rates = self.get_demand_rates(scenario_id, service_id)
        if not demand_rates:
            return None, None

        q_drs, p_drs = demand_rates.values('age_group_id', 'gender_id', 'factor')\
            .query.sql_with_params()

        #  check if the area-population is precalculated
        if pop_arealevel.up_to_date:
            areapop = self.get_areapop(
                filter_params={'area__area_level_id': area_level_id, })

            q_areapop, p_areapop = areapop.values('area_id', 'age_group_id',
                                                  'gender_id', 'value')\
                .query.sql_with_params()

            query = f'''SELECT
            a."id", a."_label", val."value"
            FROM ({q_areas}) AS a
            LEFT JOIN (
              SELECT
                ap."area_id",
                SUM(ap."value" * COALESCE(dr."factor", 0)) AS "value"
              FROM
                ({q_areapop}) AS ap
                LEFT JOIN ({q_drs}) AS dr
              ON (ap.age_group_id = dr.age_group_id
              AND ap.gender_id = dr.gender_id)
              GROUP BY ap."area_id"
            ) val ON (val."area_id" = a."id")
            '''

            params = p_areas + p_areapop + p_drs

        else:
            # calculate it from the raster cells
            rcp = RasterCellPopulation.objects.all()
            acells = AreaCell.objects.filter(area__area_level_id=area_level_id)
            rasterpop = self.get_rasterpop()

            # sum up the rastercell-population to areas
            # taking the share_area_of_cell into account
            q_acells, p_acells = acells.values(
                'area_id', 'cell_id', 'share_area_of_cell').query.sql_with_params()
            q_pop, p_pop = rasterpop.values('cell_id', 'age_group_id',
                                            'gender_id', 'value').query.sql_with_params()
            q_rcp, p_rcp = rcp.values('id', 'cell_id').query.sql_with_params()

            query = f'''SELECT
            a."id", a."_label", val."value"
            FROM ({q_areas}) AS a
            LEFT JOIN (
              SELECT
                ac."area_id",
                SUM(p."value" * dr."factor" * ac."share_area_of_cell") AS "value"
              FROM
                ({q_acells}) AS ac,
                ({q_pop}) AS p,
                ({q_rcp}) AS rcp,
                ({q_drs}) AS dr
              WHERE p."age_group_id" = dr."age_group_id"
                AND p."gender_id" = dr."gender_id"
                AND ac."cell_id" = rcp."id"
                AND p."cell_id" = rcp."cell_id"
              GROUP BY ac."area_id"
            ) val ON (val."area_id" = a."id")
            '''

            params = p_areas + p_acells + p_pop + p_rcp + p_drs
        return query, params

    def compute(self):
        """"""
        query, params = self.get_query_and_params()
        if not query:
            return []
        areas_with_demand = Area.objects.raw(query, params)
        return areas_with_demand
