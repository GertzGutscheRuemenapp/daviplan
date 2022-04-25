from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer)


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
        return []
