from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)

from datentool_backend.indicators.models import MatrixCellPlace


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
                f'{self.service.facility_article or "die"} '
                'am besten erreichbare ist)')
        ihrihm = ('ihm' if self.service.facility_singular_unit
                   in ['der', 'das'] else 'ihr')
        return pre + (
            f'die {self.service.demand_plural_unit or "Nachfragenden"} '
            f'erreicht, die von {ihrihm} aus am besten erreichbar sind')

    def compute(self):
        variant = self.data.get('variant')
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)

        q_cp, p_cp = cells_places.query.sql_with_params()

        # todo average weighted with demand
        query = f'''SELECT
        c."place_id" AS id,
        avg(c."minutes") AS value
        FROM (
        SELECT
        cp."cell_id",
        cp."place_id",
        cp."minutes",
        row_number() OVER(PARTITION BY cp."cell_id" ORDER BY cp."minutes" ASC) AS rn
        FROM
        ({q_cp}) cp
        ) c
        WHERE c.rn = 1
        GROUP BY c."place_id"
        '''
        params = p_cp
        places_with_average_minutes = Place.objects.raw(query, params)
        return places_with_average_minutes
