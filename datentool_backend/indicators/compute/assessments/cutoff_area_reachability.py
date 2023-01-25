from django.core.exceptions import BadRequest
from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       IndicatorNumberParameter,
                                                       ResultSerializer)

from datentool_backend.indicators.compute.population import PopulationIndicatorMixin
from datentool_backend.indicators.compute.reachabilities import ModeVariantMixin
from datentool_backend.population.models import AreaCell

from datentool_backend.infrastructure.models import Service
from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.area.models import Area


@register_indicator()
class CutoffAreaReachability(ModeVariantMixin, PopulationIndicatorMixin, ServiceIndicator):
    '''Anteil der Nachfragenden aus einer Gebietseinheit, welche die nächste
    Einrichtung mit der betrachteten Leistung innerhalb oder außerhalb der
    Gebietseinheit in maximal … Minuten mit einem bestimmter Verkehrsmittel
    erreichen'''
    title = 'Anteil im Gebiet mit Erreichbarkeit bis […] Minuten'
    unit = '%'
    params = (
        ModeParameter(),
        IndicatorNumberParameter('cutoff', 'maximale Wegezeit (in Minuten)',
                                 min=0, max=240, integer_only=True)
    )
    representation = 'colorramp'
    colormap_name = 'Greens'
    result_serializer = ResultSerializer.AREA

    @property
    def description(self):
        pre = (f'Anteil {self.service.demand_plural_unit}'
               ', die innerhalb von [...] Minuten ')
        if self.service.direction_way_relationship == Service.WayRelationship.TO:
            ein = ('einen' if self.service.facility_article
                   in ['der', 'das'] else 'eine')
            return pre + (
                f'{ein} {self.service.facility_singular_unit} '
                'erreichen')
        ein = ('einem' if self.service.facility_article in ['der', 'das']
               else 'einer')
        return pre + (
            f'von {ein} {self.service.facility_singular_unit} '
            'erreicht werden')

    def compute(self):
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')
        area_level_id = self.data.get('area_level')
        mode = self.data.get('mode')
        variant = self.get_mode_variant(mode, scenario_id)
        if not variant:
            return []
        cutoff = self.data.get('cutoff')

        if area_level_id is None:
            raise BadRequest('No AreaLevel provided')
        areas = self.get_areas(area_level_id=area_level_id)

        q_areas, p_areas = areas.values('id', '_label').query.sql_with_params()

        acells = AreaCell.objects.filter(area__area_level_id=area_level_id)

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)
        q_cp, p_cp = cells_places.query.sql_with_params()

        q_acells, p_acells = acells.values(
            'area_id', 'rastercellpop_id', 'share_area_of_cell').query.sql_with_params()

        q_demand, p_demand = self.get_cell_demand(scenario_id, service_id)

        if q_demand is None:
            return self.get_areas_without_values(q_areas, p_areas)

        query = f'''SELECT
            a."id", a."_label", val."value"
            FROM ({q_areas}) AS a
            LEFT JOIN (
        SELECT
        ac."area_id",
        CASE WHEN sum(d."value" * ac."share_area_of_cell") = 0
        THEN NULL
        ELSE sum((c."minutes" <= %s)::INTEGER::DOUBLE PRECISION * d."value" * ac."share_area_of_cell") /
             sum(d."value" * ac."share_area_of_cell") * 100
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
        params = p_areas + (cutoff, ) + p_cp + p_demand + p_acells

        share_of_area_demand_below_cutoff = Area.objects.raw(query, params)
        return share_of_area_demand_below_cutoff
