from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer)


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
        return []
