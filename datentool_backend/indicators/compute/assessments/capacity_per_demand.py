from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer,
                                                       )
from datentool_backend.indicators.compute.services import TotalCapacityInArea
from datentool_backend.indicators.compute.demand import DemandAreaIndicator
from datentool_backend.area.models import Area


@register_indicator()
class CapacityPerDemandInArea(ServiceIndicator):
    '''Kapazitätseinheiten für die betrachtete Leistung in einer Gebietseinheit
    pro 100 Nachfragen­den in der gleichen Gebietseinheit'''
    capacity_required = True
    title = 'Plätze pro Nachfrage'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.capacity_plural_unit or "Kapazitätseinheiten"} '
                f'pro 100 {self.service.demand_plural_unit or "Nachfragende"}')

    def compute(self):
        demand_area_indicator = DemandAreaIndicator(self.data)
        areas_with_demand = demand_area_indicator.compute()
        if not areas_with_demand:
            return []
        q_d = areas_with_demand.raw_query
        p_d = areas_with_demand.params

        capacity_indicator = TotalCapacityInArea(self.data)
        areas_with_capacity = capacity_indicator.compute()
        q_c, p_c = areas_with_capacity.query.sql_with_params()

        query = f'''SELECT
        c."id",
        CASE WHEN COALESCE(d."value", 0) = 0 THEN NULL
        ELSE COALESCE(c."value", 0) / d."value"
        END AS "value"
        FROM
        ({q_c}) c
        LEFT JOIN ({q_d}) d
        ON d."id" = c."id"
        '''
        params = p_c + p_d
        areas_with_capacity_per_demand = Area.objects.raw(query, params)
        return areas_with_capacity_per_demand
