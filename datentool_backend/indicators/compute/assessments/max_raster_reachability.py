from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)
from django.db.models import Min, F
from datentool_backend.indicators.models import MatrixCellPlace


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
            return (f'Wegezeit von allen Wohnstandorten {zu} nächsten '
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
        variant = self.data.get('variant')
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)
        cells_places_min = cells_places.values('cell').annotate(value=Min('minutes'))
        cells_places_min = cells_places_min.annotate(cell_code=F('cell__cellcode'))
        return cells_places_min
