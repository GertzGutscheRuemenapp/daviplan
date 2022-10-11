from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)

from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.infrastructure.models.places import Place, Service
from datentool_backend.indicators.compute.reachabilities import ModeVariantMixin


@register_indicator()
class MaxPlaceReachability(ModeVariantMixin, ServiceIndicator):
    '''Maximale Wegezeit der Nachfragenden aus allen Gebietseinheiten, für
    welche die betreffende Einrichtung mit einem bestimmten Verkehrsmittel
    die am schnellsten erreichbar ist'''
    title = 'Maximale Wegedauer'
    params = (ModeParameter(), )
    unit = 'Minuten'
    representation = 'colorramp'
    colormap_name = 'YlOrRd'
    result_serializer = ResultSerializer.PLACE

    @property
    def description(self):
        pre = ('Maximale Wegezeit, mit der '
               f'{self.service.facility_article} angezeigte '
               f'{self.service.facility_singular_unit} ')
        if self.service.direction_way_relationship == Service.WayRelationship.TO:
            ersiees = ('er' if self.service.facility_singular_unit == 'der'
                       else 'es' if self.service.facility_singular_unit == 'das'
                       else 'sie')
            return pre + (
                f'erreicht wird (sofern {ersiees} '
                f'{self.service.facility_article} '
                'am besten erreichbare ist)')
        ihrihm = ('ihm' if self.service.facility_singular_unit
                   in ['der', 'das'] else 'ihr')
        return pre + (
            f'die {self.service.demand_plural_unit} '
            f'erreicht, die von {ihrihm} aus am besten erreichbar sind')

    def compute(self):
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')
        mode = self.data.get('mode')
        variant = self.get_mode_variant(mode, scenario_id)

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)

        q_cp, p_cp = cells_places.query.sql_with_params()

        query = f'''SELECT
        p."place_id" AS id,
        p."minutes" AS value
        FROM (
        SELECT
        c."place_id",
        c."minutes",
        row_number() OVER(PARTITION BY c."place_id" ORDER BY c."minutes" DESC) AS rn
        FROM(
        SELECT
        cp."cell_id",
        cp."place_id",
        cp."minutes",
        row_number() OVER(PARTITION BY cp."cell_id" ORDER BY cp."minutes" ASC) AS rn
        FROM
        ({q_cp}) cp
        ) c
        WHERE c.rn = 1
        ) p
        WHERE p.rn = 1
        '''
        params = p_cp
        places_with_maximum_minutes = Place.objects.raw(query, params)
        return places_with_maximum_minutes
