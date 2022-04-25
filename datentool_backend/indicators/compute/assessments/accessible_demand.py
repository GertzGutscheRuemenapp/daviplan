from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)


@register_indicator()
class AccessibleDemandPerArea(ServiceIndicator):
    '''Anzahl der Nachfragenden nach der betrachteten Leistung aus allen
    Gebietseinheiten, für welche die betreffende Einrichtung mit dieser Leistung
    am besten mit einem bestimmten Verkehrsmittel erreichbar ist.'''
    title = 'Nachfrage im Einzugsbereich'
    params = (ModeParameter(), )
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'Anzahl {self.service.demand_plural_unit or "Nachfragende"}, '
                f'für die {self.service.facility_article or "die"} angezeigte '
                f'{self.service.facility_singular_unit or "Einrichtung"} '
                f'{self.service.facility_article or "die"} am besten '
                'erreichbare ist')

    def compute(self):
        return []
