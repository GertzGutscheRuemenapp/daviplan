from .base import (AreaAssessmentIndicator, register_indicator,
                   RasterAssessmentIndicator, PlaceAssessmentIndicator,
                   CapacityRequirement)


@register_indicator()
class DemandAreaCapacity(AreaAssessmentIndicator):
    description = ('Nachfragende nach betrachteter Leistung in einer '
                   'Gebietseinheit pro Kapazitätseinheit für diese Leistung in '
                   'der gleichen Gebietseinheit')
    capacity_required = CapacityRequirement.required
    title = 'Nachfrage pro Einrichtung'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class DemandArea(AreaAssessmentIndicator):
    description = ('Nachfragende nach betrachteter Leistung in einer '
                   'Gebietseinheit pro Einrichtung mit dieser Leistung in der '
                   'gleichen Gebietseinheit')
    capacity_required = CapacityRequirement.not_required
    title = 'Nachfrage pro Platz'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class DemandArea(AreaAssessmentIndicator):
    description = ('Nachfragende nach betrachteter Leistung in einer '
                   'Gebietseinheit pro Einrichtung mit dieser Leistung in der '
                   'gleichen Gebietseinheit')
    capacity_required = CapacityRequirement.independent
    title = 'Nachfrage im Einzugsbereich'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class SupplyAreaCapacity(AreaAssessmentIndicator):
    description = ('Kapazitätseinheiten für die betrachtete Leistung in einer '
                   'Gebietseinheit pro 100 Nachfragen­den in der gleichen '
                   'Gebietseinheit')
    capacity_required = CapacityRequirement.required
    title = 'Einrichtungen pro Nachfrage'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class SupplyArea(AreaAssessmentIndicator):
    description = ('Einrichtungen mit der betrachteten Leistung in einer '
                   'Gebietseinheit pro Nachfragen­de in der gleichen '
                   'Gebietseinheit')
    capacity_required = CapacityRequirement.not_required
    title = 'Plätze pro Nachfrage'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class AverageAreaReachability(AreaAssessmentIndicator):
    description = ('Mittlerer Zeitaufwand der Nachfragenden aus einer '
                   'Gebietseinheit, um mit einem bestimmten Verkehrsmittel die '
                   'nächste Einrichtung mit der betrachteten Leistung zu '
                   'erreichen')
    capacity_required = CapacityRequirement.independent
    title = 'Mittlere Wegedauer'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class CutoffAreaReachability(AreaAssessmentIndicator):
    description = ('Anteil der Nachfragenden aus einer Gebietseinheit, welche '
                   'die nächste Einrichtung mit der betrachteten Leistung '
                   'innerhalb oder außerhalb der Gebietseinheit in maximal … '
                   'Minuten mit einem bestimmter Verkehrsmittel erreichen')
    capacity_required = CapacityRequirement.independent
    title = 'Erreichbarkeit bis … Minuten'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class AveragePlaceReachability(PlaceAssessmentIndicator):
    description = ('Mittlere Wegezeit der Nachfragenden aus allen '
                   'Gebietseinheiten, für welche die betreffende Einrichtung '
                   'mit einem bestimmten Verkehrsmittel die am schnellsten '
                   'erreichbar ist')
    capacity_required = CapacityRequirement.independent
    title = 'Mittlere Erreichbarkeit'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class MaxPlaceReachability(PlaceAssessmentIndicator):
    description = ('Maximale Wegezeit der Nachfragenden aus allen '
                   'Gebietseinheiten, für welche die betreffende Einrichtung '
                   'mit einem bestimmten Verkehrsmittel die am schnellsten '
                   'erreichbar ist')
    capacity_required = CapacityRequirement.independent
    title = 'Maximale Wegedauer'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass


@register_indicator()
class MaxPlaceReachability(RasterAssessmentIndicator):
    description = ('Wegzeit mit Verkehrsmittel zur nächsten Einrichtung mit …. '
                   'für alle Wohnstandorte')
    capacity_required = CapacityRequirement.independent
    title = 'Wegzeit nächste Einrichtung'

    @property
    def detailed_title(self):
        return ''

    def compute(self, query_params):
        pass
