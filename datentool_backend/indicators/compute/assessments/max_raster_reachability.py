from datentool_backend.indicators.compute.base import (register_indicator,
                                                       ServiceIndicator,
                                                       ModeParameter,
                                                       ResultSerializer)
from django.db.models import Min, F
from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.infrastructure.models import Service
from datentool_backend.indicators.compute.reachabilities import ModeVariantMixin


@register_indicator()
class MaxRasterReachability(ModeVariantMixin, ServiceIndicator):
    '''Wegezeit mit Verkehrsmittel zur nächsten Einrichtung mit ….
    für alle Wohnstandorte'''
    title = 'Wegezeit Wohnstandort zur nächsten Einrichtung'
    params = (ModeParameter(), )
    representation = 'colorramp'
    colormap_name = 'RdYlGn'
    inverse = True
    digits = 0
    result_serializer = ResultSerializer.RASTER
    unit = 'Minuten'

    @property
    def description(self):
        if self.service.direction_way_relationship == Service.WayRelationship.TO:
            zu = ('zum' if self.service.facility_article in ['der', 'das']
                  else 'zur')
            return (f'Wegezeit von allen Wohnstandorten {zu} nächsten '
                    f'{self.service.facility_singular_unit}')
        derdem = ('dem' if self.service.facility_article in ['der', 'das']
                   else 'der')
        ersiees = ('er' if self.service.facility_article == 'der'
                   else 'es' if self.service.facility_article == 'das'
                   else 'sie')
        return (f'Wegezeit zu allen Wohnstandorten ab {derdem} nächsten '
                f'{self.service.facility_singular_unit}, '
                f'die {ersiees} am schnellsten erreicht')

    def compute(self):
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')
        mode = self.data.get('mode')
        variant = self.get_mode_variant(mode, scenario_id)

        places = self.get_places_with_capacities(service_id, year, scenario_id)
        cells_places = MatrixCellPlace.objects.filter(variant=variant, place__in=places)
        cells_places_min = cells_places.values('cell').annotate(value=Min('minutes'))
        cells_places_min = cells_places_min.annotate(cell_code=F('cell__cellcode'))
        return cells_places_min
