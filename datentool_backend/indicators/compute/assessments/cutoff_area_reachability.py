from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       IndicatorNumberParameter,
                                                       ResultSerializer)


@register_indicator()
class CutoffAreaReachability(ServiceIndicator):
    '''Anteil der Nachfragenden aus einer Gebietseinheit, welche die nächste
    Einrichtung mit der betrachteten Leistung innerhalb oder außerhalb der
    Gebietseinheit in maximal … Minuten mit einem bestimmter Verkehrsmittel
    erreichen'''
    title = 'Erreichbarkeit bis […] Minuten'
    params = (
        ModeParameter(),
        IndicatorNumberParameter('cutoff', 'maximale Wegezeit (in Minuten)',
                                 min=0, max=240, integer_only=True)
    )
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        pre = (f'Anteil der {self.service.demand_plural_unit or "Nachfragenden"}'
               ', die innerhalb von [...] Minuten ')
        if self.service.direction_way_relationship == 1:
            ein = ('einen' if self.service.facility_singular_unit
                   in ['der', 'das'] else 'eine')
            return pre + (
                f'{ein} {self.service.facility_singular_unit or "Einrichtung"} '
                'erreichen')
        ein = ('einem' if self.service.facility_singular_unit in ['der', 'das']
               else 'einer')
        return pre + (
            f'von {ein} {self.service.facility_singular_unit or "Einrichtung"} '
            'erreicht werden')

    def compute(self):
        return []
