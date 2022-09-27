from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer)

from datentool_backend.indicators.compute.demand import DemandAreaIndicator
from datentool_backend.indicators.compute.services import TotalCapacityInArea
from datentool_backend.area.models import Area


@register_indicator()
class DemandPerCapacity(ServiceIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Kapazitätseinheit für diese Leistung in der gleichen Gebietseinheit'''
    capacity_required = True
    title = 'Nachfrage pro Platz'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.demand_plural_unit} pro '
                f'{self.service.capacity_singular_unit}')

    def compute(self):
        demand_area_indicator = DemandAreaIndicator(self.data)
        areas_with_demand = demand_area_indicator.compute()
        if not areas_with_demand:
            return []
        q_d = areas_with_demand.raw_query
        p_d = areas_with_demand.params

        capacity_in_area = TotalCapacityInArea(self.data)
        areas_with_capacity = capacity_in_area.compute()
        q_l, p_l = areas_with_capacity.query.sql_with_params()

        query = f'''SELECT
        l."id",
        d."_label",
        CASE WHEN COALESCE(l."value", 0) = 0 THEN NULL
        ELSE d."value" / l."value"
        END AS "value"
        FROM
        ({q_l}) l
        LEFT JOIN ({q_d}) d
        ON d."id" = l."id"
        '''
        params = p_l + p_d
        areas_with_demand_per_capacity = Area.objects.raw(query, params)
        return areas_with_demand_per_capacity
