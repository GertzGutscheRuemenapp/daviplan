from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)


@register_indicator()
class AverageAreaReachability(ServiceIndicator):
    '''Mittlerer Zeitaufwand der Nachfragenden aus einer Gebietseinheit, um mit
    einem bestimmten Verkehrsmittel die nächste Einrichtung mit der betrachteten
    Leistung zu erreichen'''
    title = 'Mittlere Wegedauer'
    params = (ModeParameter(), )
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        zu = ('zum' if self.service.facility_singular_unit in ['der', 'das']
              else 'zur')
        return (f'Mittlere Wegezeit {zu} besterreichbaren '
                f'{self.service.facility_singular_unit or "Einrichtung"}')
    def compute(self):
        return []
