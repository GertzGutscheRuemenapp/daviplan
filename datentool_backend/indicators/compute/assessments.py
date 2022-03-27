from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ResultSerializer,
                                                       IndicatorChoiceParameter,
                                                       IndicatorNumberParameter)

from datentool_backend.modes.models import Mode


class ModeParameter(IndicatorChoiceParameter):
    name = 'mode'
    title = 'Verkehrsmittel'
    choices = Mode.choices
    def __init__(self):
        super().__init__(self.name, self.choices, title=self.title)


@register_indicator()
class DemandAreaCapacity(ServiceIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Kapazitätseinheit für diese Leistung in der gleichen Gebietseinheit'''
    capacity_required = True
    title = 'Nachfrage pro Einrichtung'
    result_serializer = ResultSerializer.AREA
    @property
    def description(self):
        return (f'{self.service.demand_plural_unit or "Nachfragende"} pro '
                f'{self.service.facility_singular_unit or "Einrichtung"}')

    def compute(self):
        return []


@register_indicator()
class DemandArea(ServiceIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Einrichtung mit dieser Leistung in der gleichen Gebietseinheit'''
    title = 'Nachfrage pro Platz'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.demand_plural_unit or "Nachfragende"} pro '
                f'{self.service.capacity_singular_unit or "Kapazitätseinheit"}')

    def compute(self):
        return []


@register_indicator()
class ReachabilityDemandArea(ServiceIndicator):
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


@register_indicator()
class SupplyAreaCapacity(ServiceIndicator):
    '''Kapazitätseinheiten für die betrachtete Leistung in einer Gebietseinheit
    pro 100 Nachfragen­den in der gleichen Gebietseinheit'''
    capacity_required = True
    title = 'Einrichtungen pro Nachfrage'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.facility_plural_unit or "Einrichtungen"} pro '
                f'100 {self.service.demand_plural_unit or "Nachfragende"}')

    def compute(self):
        return []


@register_indicator()
class SupplyArea(ServiceIndicator):
    '''Einrichtungen mit der betrachteten Leistung in einer Gebietseinheit pro
    Nachfragen­de in der gleichen Gebietseinheit'''
    title = 'Plätze pro Nachfrage'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        return (f'{self.service.capacity_plural_unit or "Kapazitätseinheiten"} '
                f'pro 100 {self.service.demand_plural_unit or "Nachfragende"}')

    def compute(self):
        return []


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


@register_indicator()
class AveragePlaceReachability(ServiceIndicator):
    '''Mittlere Wegezeit der Nachfragenden aus allen Gebietseinheiten, für
    welche die betreffende Einrichtung mit einem bestimmten Verkehrsmittel die
    am schnellsten erreichbar ist'''
    title = 'Mittlere Erreichbarkeit'
    params = (ModeParameter(), )
    result_serializer = ResultSerializer.PLACE

    @property
    def description(self):
        pre = ('Mittlere Wegezeit, mit der '
               f'{self.service.facility_article or "die"} angezeigte '
               f'{self.service.facility_singular_unit or "Einrichtung"} ')
        if self.service.direction_way_relationship == 1:
            ersiees = ('er' if self.service.facility_singular_unit == 'der'
                       else 'es' if self.service.facility_singular_unit == 'das'
                       else 'sie')
            return pre + (
                f'erreicht wird (sofern {ersiees} '
                f'{self.service.facility_singular_unit or "die"} '
                'am besten erreichbare ist)')
        ihrihm = ('ihm' if self.service.facility_singular_unit
                   in ['der', 'das'] else 'ihr')
        return pre +  (
            f'die {self.service.demand_plural_unit or "Nachfragenden"} '
            f'erreicht, die von {ihrihm} aus am besten erreichbar sind')

    def compute(self):
        return []


@register_indicator()
class MaxPlaceReachability(ServiceIndicator):
    '''Maximale Wegezeit der Nachfragenden aus allen Gebietseinheiten, für
    welche die betreffende Einrichtung mit einem bestimmten Verkehrsmittel
    die am schnellsten erreichbar ist'''
    title = 'Maximale Wegedauer'
    params = (ModeParameter(), )
    result_serializer = ResultSerializer.PLACE

    @property
    def description(self):
        pre = ('Maximale Wegezeit, mit der '
               f'{self.service.facility_article or "die"} angezeigte '
               f'{self.service.facility_singular_unit or "Einrichtung"} ')
        if self.service.direction_way_relationship == 1:
            ersiees = ('er' if self.service.facility_singular_unit == 'der'
                       else 'es' if self.service.facility_singular_unit == 'das'
                       else 'sie')
            return pre + (
                f'erreicht wird (sofern {ersiees} '
                f'{self.service.facility_singular_unit or "die"} '
                'am besten erreichbare ist)')
        ihrihm = ('ihm' if self.service.facility_singular_unit
                   in ['der', 'das'] else 'ihr')
        return pre +  (
            f'die {self.service.demand_plural_unit or "Nachfragenden"} '
            f'erreicht, die von {ihrihm} aus am besten erreichbar sind')

    def compute(self):
        return []


@register_indicator()
class MaxRasterReachability(ServiceIndicator):
    '''Wegezeit mit Verkehrsmittel zur nächsten Einrichtung mit ….
    für alle Wohnstandorte'''
    title = 'Wegezeit nächste Einrichtung'
    params = (ModeParameter(), )
    result_serializer = ResultSerializer.RASTER

    @property
    def description(self):
        if self.service.direction_way_relationship == 1:
            zu = ('zum' if self.service.facility_singular_unit in ['der', 'das']
                  else 'zur')
            return (f'Wegezeit von allen Wohnstandorten {zu} nächsten'
                    f'{self.service.facility_singular_unit or "Einrichtung"}')
        derdem = ('dem' if self.service.facility_singular_unit in ['der', 'das']
                   else 'der')
        ersiees = ('er' if self.service.facility_singular_unit == 'der'
                   else 'es' if self.service.facility_singular_unit == 'das'
                   else 'sie')
        return (f'Wegezeit zu allen Wohnstandorten ab {derdem} nächsten '
                f'{self.service.facility_singular_unit or "Einrichtung"}, '
                f'die {ersiees} am schnellsten erreicht')

    def compute(self):
        return []
