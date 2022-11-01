from django.core.exceptions import BadRequest

from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)

from datentool_backend.indicators.compute.population import PopulationIndicatorMixin
from datentool_backend.indicators.compute.reachabilities import ModeVariantMixin
from datentool_backend.population.models import AreaCell

from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.area.models import Area


@register_indicator()
class AverageAreaReachability(ModeVariantMixin, PopulationIndicatorMixin, ServiceIndicator):
    '''Mittlerer Zeitaufwand der Nachfragenden aus einer Gebietseinheit, um mit
    einem bestimmten Verkehrsmittel die nächste Einrichtung mit der betrachteten
    Leistung zu erreichen'''
    title = 'Mittlere Wegedauer der Nachfragenden im Gebiet'
    params = (ModeParameter(), )
    representation = 'colorramp'
    colormap_name = 'Reds'
    result_serializer = ResultSerializer.AREA
    unit = 'Minuten'

    @property
    def description(self):
        zu = ('zum' if self.service.facility_singular_unit in ['der', 'das']
              else 'zur')
        return (f'Mittlere Wegezeit {zu} besterreichbaren '
                f'{self.service.facility_singular_unit}')

    def compute(self):
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')
        area_level_id = self.data.get('area_level')
        mode = self.data.get('mode')
        variant = self.get_mode_variant(mode, scenario_id)

        if area_level_id is None:
            raise BadRequest('No AreaLevel provided')
        areas = self.get_areas(area_level_id=area_level_id)

        q_areas, p_areas = areas.values('id', '_label').query.sql_with_params()

        acells = AreaCell.objects.filter(area__area_level_id=area_level_id)

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)
        q_cp, p_cp = cells_places.query.sql_with_params()

        q_demand, p_demand = self.get_cell_demand(scenario_id, service_id)
        if not p_demand:
            return self.get_areas_without_values(q_areas, p_areas)

        q_acells, p_acells = acells.values(
            'area_id', 'rastercellpop_id', 'share_area_of_cell').query.sql_with_params()

        query = f'''SELECT
            a."id", a."_label", val."value"
            FROM ({q_areas}) AS a
            LEFT JOIN (
        SELECT
        ac."area_id",
        CASE WHEN sum(d."value" * ac."share_area_of_cell") = 0
        THEN NULL
        ELSE sum(c."minutes" * d."value" * ac."share_area_of_cell") /
             sum(d."value" * ac."share_area_of_cell")
        END AS value
        FROM (
        SELECT
        cp."cell_id",
        cp."place_id",
        cp."minutes",
        row_number() OVER(PARTITION BY cp."cell_id" ORDER BY cp."minutes" ASC) AS rn
        FROM
        ({q_cp}) cp
        ) c,
        ({q_demand}) d,
        ({q_acells}) AS ac
        WHERE c.rn = 1
        AND c."cell_id" = d."cell_id"
        AND ac."rastercellpop_id" = d."rastercellpop_id"
        GROUP BY ac."area_id"
        ) val ON (val."area_id" = a."id")
        '''
        params = p_areas + p_cp + p_demand + p_acells
        area_with_average_minutes = Area.objects.raw(query, params)
        return area_with_average_minutes

