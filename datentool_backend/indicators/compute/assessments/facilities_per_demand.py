from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer)


@register_indicator()
class FacilitiesPerDemandInArea(ServiceIndicator):
    '''Einrichtungen mit der betrachteten Leistung in einer Gebietseinheit pro
    Nachfragen­de in der gleichen Gebietseinheit'''
    title = 'Einrichtungen pro Nachfrage'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.facility_plural_unit or "Einrichtungen"} pro '
                f'100 {self.service.demand_plural_unit or "Nachfragende"}')

    def compute(self):
        return []
