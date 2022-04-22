from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer)


@register_indicator()
class DemandAreaCapacity(ServiceIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Kapazitätseinheit für diese Leistung in der gleichen Gebietseinheit'''
    capacity_required = True
    title = 'Nachfrage pro Platz'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.demand_plural_unit or "Nachfragende"} pro '
                f'{self.service.capacity_singular_unit or "Kapazitätseinheit"}')

    def compute(self):
        return []

