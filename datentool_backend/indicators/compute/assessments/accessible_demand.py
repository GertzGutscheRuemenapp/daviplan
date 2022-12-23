from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)
from datentool_backend.indicators.compute.population import PopulationIndicatorMixin
from datentool_backend.indicators.compute.reachabilities import ModeVariantMixin

from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.places.models import Place


@register_indicator()
class AccessibleDemandPerPlace(ModeVariantMixin, PopulationIndicatorMixin, ServiceIndicator):
    '''Anzahl der Nachfragenden nach der betrachteten Leistung aus allen
    Gebietseinheiten, für welche die betreffende Einrichtung mit dieser Leistung
    am besten mit einem bestimmten Verkehrsmittel erreichbar ist.'''
    title = 'Nachfrage im Einzugsbereich der Einrichtung'
    params = (ModeParameter(), )
    representation = 'colorramp'
    colormap_name = 'PuBu'
    result_serializer = ResultSerializer.PLACE

    @property
    def description(self):
        return (f'Anzahl {self.service.demand_plural_unit}, '
                f'für die {self.service.facility_article} angezeigte '
                f'{self.service.facility_singular_unit} '
                f'{self.service.facility_article} am besten '
                'erreichbare ist')

    def compute(self):
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')
        mode = self.data.get('mode')
        variant = self.get_mode_variant(mode, scenario_id)

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)
        q_cp, p_cp = cells_places.query.sql_with_params()

        q_demand, p_demand = self.get_cell_demand(scenario_id, service_id)

        if not p_demand:
            return []

        query = f'''SELECT
        c."place_id" AS id,
        sum(d."value") AS "value"
        FROM (
        SELECT
        cp."cell_id",
        cp."place_id",
        cp."minutes",
        row_number() OVER(PARTITION BY cp."cell_id" ORDER BY cp."minutes" ASC) AS rn
        FROM
        ({q_cp}) cp
        ) c,
        ({q_demand}) d
        WHERE c.rn = 1
        AND c."cell_id" = d."cell_id"
        GROUP BY c."place_id"
        '''
        params = p_cp + p_demand
        places_with_demand = Place.objects.raw(query, params)
        return places_with_demand
