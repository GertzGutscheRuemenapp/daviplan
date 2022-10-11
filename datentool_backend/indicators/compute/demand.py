from datentool_backend.indicators.compute.base import ComputeIndicator, ResultSerializer
from datentool_backend.indicators.compute.population import PopulationIndicatorMixin
from datentool_backend.area.models import Area


class DemandAreaIndicator(PopulationIndicatorMixin,
                          ComputeIndicator):
    label = 'Demand for Service By Area'
    description = 'Total Demand for Service per Area'
    representation = 'colorramp'
    colormap_name = 'Blues'
    result_serializer = ResultSerializer.AREA

    def compute(self):
        """"""
        scenario_id = self.data.get('scenario')
        service_id = self.data.get('service')
        area_level_id = self.data.get('area_level')
        query, params = self.get_area_demand(scenario_id, service_id, area_level_id)
        if not query:
            return []
        areas_with_demand = Area.objects.raw(query, params)
        return areas_with_demand
