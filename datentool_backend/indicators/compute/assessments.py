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
        return ''

    def compute(self):
        return []


@register_indicator()
class DemandArea(AreaAssessmentIndicator):
    '''Nachfragende nach betrachteter Leistung in einer Gebietseinheit pro
    Einrichtung mit dieser Leistung in der gleichen Gebietseinheit'''
    title = 'Nachfrage pro Platz'

    @property
    def description(self):
        return ''

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
        return ''

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
        return ''

    def compute(self):
        return []


@register_indicator()
class SupplyArea(AreaAssessmentIndicator):
    '''Einrichtungen mit der betrachteten Leistung in einer Gebietseinheit pro
    Nachfragen­de in der gleichen Gebietseinheit'''
    title = 'Plätze pro Nachfrage'

    @property
    def description(self):
        return ''

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
        return ''

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
        return ''

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
        return ''

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
        return ''

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
