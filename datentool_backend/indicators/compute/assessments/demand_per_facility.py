from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer)

from datentool_backend.indicators.compute.demand import DemandAreaIndicator
from datentool_backend.indicators.compute.services import NumberOfLocations
from datentool_backend.area.models import Area


@register_indicator()
class DemandPerFacility(ServiceIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Einrichtung mit dieser Leistung in der gleichen Gebietseinheit'''
    title = 'Nachfrage pro Einrichtung'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.demand_plural_unit or "Nachfragende"} pro '
                f'{self.service.facility_singular_unit or "Einrichtung"}')

    def compute(self):
        demand_area_indicator = DemandAreaIndicator(self.data)
        areas_with_demand = demand_area_indicator.compute()
        if not areas_with_demand:
            return []
        q_d = areas_with_demand.raw_query
        p_d = areas_with_demand.params

        num_locations = NumberOfLocations(self.data)
        areas_with_locations = num_locations.compute()
        q_l, p_l = areas_with_locations.query.sql_with_params()

        query = f'''SELECT
        l."id",
        CASE WHEN COALESCE(l."value", 0) = 0 THEN NULL
        ELSE COALESCE(d."value", 0) / l."value"
        END AS "value"
        FROM
        ({q_l}) l
        LEFT JOIN ({q_d}) d
        ON d."id" = l."id"
        '''
        params = p_l + p_d
        areas_with_demand_per_facility = Area.objects.raw(query, params)
        return areas_with_demand_per_facility
