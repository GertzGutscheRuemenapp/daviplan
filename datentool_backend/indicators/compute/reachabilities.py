from django.db.models import F

from datentool_backend.indicators.compute.base import (ComputeIndicator,
                                                       ResultSerializer)
from datentool_backend.modes.models import Mode, ModeVariant
from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.infrastructure.models.places import Place


class ReachabilityPlace(ComputeIndicator):
    '''Wegezeit zwischen ausgewählter Einrichtung und allen Wohnstandorten
    (= Rasterzellen)'''
    title = 'Erreichbarkeit Einrichtung'
    description = ('Wegezeit zwischen ausgewählter Einrichtung und allen '
                   'Wohnstandorten (= Rasterzellen) ')
    result_serializer = ResultSerializer.RASTER

    def compute(self):
        mode = getattr(Mode, self.data.get('mode', 'WALK').upper())
        variant = ModeVariant.objects.get(mode=mode, network__name='Basisnetz')
        place = Place.objects.get(id=self.data.get('place'))
        cells = MatrixCellPlace.objects.filter(variant=variant, place=place)
        cells = cells.annotate(cell_code=F('cell__cellcode'), value=F('minutes'))
        return cells


class ReachabilityCell(ComputeIndicator):
    '''Wegezeit zwischen ausgewähltem Wohnstandort (= Rasterzelle) und allen
    Einrichtungen'''
    title = 'Erreichbarkeit Wohnstandort'
    description = ('Wegezeit zwischen ausgewähltem Wohnstandort (= Rasterzelle) '
                   'und allen Einrichtungen')
    result_serializer = ResultSerializer.PLACE

    def compute(self):
        return []