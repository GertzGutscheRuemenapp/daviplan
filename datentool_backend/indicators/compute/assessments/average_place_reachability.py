from typing import Tuple

from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)
from datentool_backend.indicators.compute.population import PopulationIndicatorMixin
from datentool_backend.population.models import RasterCellPopulation

from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.infrastructure.models.places import Place


@register_indicator()
class AveragePlaceReachability(PopulationIndicatorMixin, ServiceIndicator):
    '''Mittlere Wegezeit der Nachfragenden aus allen Gebietseinheiten, für
    welche die betreffende Einrichtung mit einem bestimmten Verkehrsmittel die
    am schnellsten erreichbar ist'''
    title = 'Mittlere Erreichbarkeit'
    params = (ModeParameter(), )
    result_serializer = ResultSerializer.PLACE

    @property
    def description(self):
        pre = ('Mittlere Wegezeit, mit der '
               f'{self.service.facility_article or "die"} angezeigte '
               f'{self.service.facility_singular_unit or "Einrichtung"} ')
        if self.service.direction_way_relationship == 1:
            ersiees = ('er' if self.service.facility_singular_unit == 'der'
                       else 'es' if self.service.facility_singular_unit == 'das'
                       else 'sie')
            return pre + (
                f'erreicht wird (sofern {ersiees} '
                f'{self.service.facility_article or "die"} '
                'am besten erreichbare ist)')
        ihrihm = ('ihm' if self.service.facility_singular_unit
                   in ['der', 'das'] else 'ihr')
        return pre + (
            f'die {self.service.demand_plural_unit or "Nachfragenden"} '
            f'erreicht, die von {ihrihm} aus am besten erreichbar sind')

    def compute(self):
        variant = self.data.get('variant')
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)
        q_cp, p_cp = cells_places.query.sql_with_params()

        q_demand, p_demand = self.get_demand(scenario_id, service_id)

        # todo average weighted with demand
        query = f'''SELECT
        c."place_id" AS id,
        CASE WHEN sum(d."value") = 0
        THEN NULL
        ELSE sum(c."minutes" * d."value") / sum(d."value")
        END AS value
        FROM (
        SELECT
        cp."cell_id",
        cp."place_id",
        cp."minutes",
        row_number() OVER(PARTITION BY cp."cell_id" ORDER BY cp."minutes" ASC) AS rn
        FROM
        ({q_cp}) cp
        ) c,
        ({q_demand}) d
        WHERE c.rn = 1
        AND c."cell_id" = d."cell_id"
        GROUP BY c."place_id"
        '''
        params = p_cp + p_demand
        places_with_average_minutes = Place.objects.raw(query, params)
        return places_with_average_minutes

    def get_demand(self, scenario_id: int, service_id: int) -> Tuple[str, Tuple[float]]:

        """get the demand per rastercell for service in scenario"""
        # calculate it from the raster cells
        rcp = RasterCellPopulation.objects.all()
        rasterpop = self.get_rasterpop()

        demand_rates = self.get_demand_rates(scenario_id, service_id)
        if not demand_rates:
            return None, None

        q_drs, p_drs = demand_rates.values('age_group_id', 'gender_id', 'factor')\
            .query.sql_with_params()


        q_pop, p_pop = rasterpop.values('cell_id', 'age_group_id',
                                        'gender_id', 'value').query.sql_with_params()
        q_rcp, p_rcp = rcp.values('id', 'cell_id').query.sql_with_params()

        q_demand = f'''SELECT
            p."cell_id",
            SUM(p."value" * dr."factor") AS "value"
          FROM
            ({q_pop}) AS p,
            ({q_rcp}) AS rcp,
            ({q_drs}) AS dr
          WHERE p."age_group_id" = dr."age_group_id"
            AND p."gender_id" = dr."gender_id"
            AND p."cell_id" = rcp."cell_id"
          GROUP BY p."cell_id"
        '''

        p_demand = p_pop + p_rcp + p_drs

        return q_demand, p_demand