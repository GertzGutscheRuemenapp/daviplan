from .base import (AreaAssessmentIndicator, register_indicator,
                   RasterAssessmentIndicator, PlaceAssessmentIndicator)


@register_indicator()
class DemandAreaCapacity(AreaAssessmentIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Kapazitätseinheit für diese Leistung in der gleichen Gebietseinheit'''
    capacity_required = True
    title = 'Nachfrage pro Einrichtung'

    @property
    def description(self):
        return (f'{self.service.demand_plural_unit or "Nachfragende"} pro '
                f'{self.service.facility_singular_unit or "Einrichtung"}')

    def compute(self):
        return []


@register_indicator()
class DemandArea(AreaAssessmentIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Einrichtung mit dieser Leistung in der gleichen Gebietseinheit'''
    title = 'Nachfrage pro Platz'

    @property
    def description(self):
        return (f'{self.service.demand_plural_unit or "Nachfragende"} pro '
                f'{self.service.capacity_singular_unit or "Kapazitätseinheit"}')

    def compute(self):
        return []


@register_indicator()
class ReachabilityDemandArea(AreaAssessmentIndicator):
    '''Anzahl der Nachfragenden nach der betrachteten Leistung aus allen
    Gebietseinheiten, für welche die betreffende Einrichtung mit dieser Leistung
    am besten mit einem bestimmten Verkehrsmittel erreichbar ist.'''
    title = 'Nachfrage im Einzugsbereich'

    @property
    def description(self):
        return (f'Anzahl {self.service.demand_plural_unit or "Nachfragende"}, '
                f'für die {self.service.facility_article or "die"} angezeigte '
                f'{self.service.facility_singular_unit or "Einrichtung"} '
                f'{self.service.facility_article or "die"} besterreichbarste '
                'ist')

    def compute(self):
        return []


@register_indicator()
class SupplyAreaCapacity(AreaAssessmentIndicator):
    '''Kapazitätseinheiten für die betrachtete Leistung in einer Gebietseinheit
    pro 100 Nachfragen­den in der gleichen Gebietseinheit'''
    capacity_required = True
    title = 'Einrichtungen pro Nachfrage'

    @property
    def description(self):
        return (f'{self.service.facility_plural_unit or "Einrichtungen"} pro '
                f'100 {self.service.demand_plural_unit or "Nachfragende"}')

    def compute(self):
        return []


@register_indicator()
class SupplyArea(AreaAssessmentIndicator):
    '''Einrichtungen mit der betrachteten Leistung in einer Gebietseinheit pro
    Nachfragen­de in der gleichen Gebietseinheit'''
    title = 'Plätze pro Nachfrage'

    @property
    def description(self):
        return (f'{self.service.capacity_plural_unit or "Kapazitätseinheiten"} '
                f'pro 100 {self.service.demand_plural_unit or "Nachfragende"}')

    def compute(self):
        return []


@register_indicator()
class AverageAreaReachability(AreaAssessmentIndicator):
    '''Mittlerer Zeitaufwand der Nachfragenden aus einer Gebietseinheit, um mit
    einem bestimmten Verkehrsmittel die nächste Einrichtung mit der betrachteten
    Leistung zu erreichen'''
    title = 'Mittlere Wegedauer'

    @property
    def description(self):
        zu = ('zum' if self.service.facility_singular_unit in ['der', 'das']
              else 'zur')
        return (f'Mittlere Wegezeit {zu} besterreichbaren '
                f'{self.service.facility_singular_unit or "Einrichtung"}')
    def compute(self):
        return []


@register_indicator()
class CutoffAreaReachability(AreaAssessmentIndicator):
    '''Anteil der Nachfragenden aus einer Gebietseinheit, welche die nächste
    Einrichtung mit der betrachteten Leistung innerhalb oder außerhalb der
    Gebietseinheit in maximal … Minuten mit einem bestimmter Verkehrsmittel
    erreichen'''
    title = 'Erreichbarkeit bis … Minuten'

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
class AveragePlaceReachability(PlaceAssessmentIndicator):
    '''Mittlere Wegezeit der Nachfragenden aus allen Gebietseinheiten, für
    welche die betreffende Einrichtung mit einem bestimmten Verkehrsmittel die
    am schnellsten erreichbar ist'''
    title = 'Mittlere Erreichbarkeit'

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
                'besterreichbare ist)')
        ihrihm = ('ihm' if self.service.facility_singular_unit
                   in ['der', 'das'] else 'ihr')
        return pre +  (
            f'die {self.service.demand_plural_unit or "Nachfragenden"} '
            f'erreicht, die von {ihrihm} aus am besten erreichbar sind')

    def compute(self):
        return []


@register_indicator()
class MaxPlaceReachability(PlaceAssessmentIndicator):
    '''Maximale Wegezeit der Nachfragenden aus allen Gebietseinheiten, für
    welche die betreffende Einrichtung mit einem bestimmten Verkehrsmittel
    die am schnellsten erreichbar ist'''
    title = 'Maximale Wegedauer'

    @property
    def description(self):
        return (f'{self.service.demand_plural_unit or "Nachfragende"} pro '
                f'{self.service.capacity_singular_unit or "Kapazitätseinheit"}')

    def compute(self):
        return []


@register_indicator()
class MaxRasterReachability(RasterAssessmentIndicator):
    '''Wegzeit mit Verkehrsmittel zur nächsten Einrichtung mit ….
    für alle Wohnstandorte'''
    title = 'Wegzeit nächste Einrichtung'

    @property
    def description(self):
        return ''

    def compute(self):
        return []
