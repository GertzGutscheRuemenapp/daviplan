from django.db.models import F, Min

from datentool_backend.indicators.compute.base import (ComputeIndicator,
                                                       ResultSerializer)
from datentool_backend.modes.models import Mode, ModeVariant
from datentool_backend.user.models.process import ScenarioMode, Scenario
from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.infrastructure.models.places import Place, Capacity


class ModeVariantMixin:
    def get_mode_variant(self, mode: Mode, scenario_id: int = None) -> ModeVariant:
        """get the mode variant"""

        scenario_modevariant = ScenarioMode.objects.filter(scenario=scenario_id,
                                                           variant__mode=mode)
        if not scenario_modevariant:
            scenario_modevariant = ScenarioMode.objects\
                .filter(variant__mode=mode)
        if scenario_modevariant:
            variant = scenario_modevariant.first().variant
        else:
            variant = ModeVariant.objects.get(mode=mode,
                                              is_default=True)
        return variant


class ReachabilityPlace(ModeVariantMixin, ComputeIndicator):
    '''Wegezeit zwischen ausgewählter Einrichtung und allen Wohnstandorten
    (= Rasterzellen)'''
    title = 'Erreichbarkeit Einrichtung'
    description = ('Wegezeit zwischen ausgewählter Einrichtung und allen '
                   'Wohnstandorten (= Rasterzellen) ')
    result_serializer = ResultSerializer.RASTER

    def compute(self):
        mode = self.data.get('mode', Mode.WALK)
        scenario_id = self.data.get('scenario')
        variant = self.get_mode_variant(mode, scenario_id)

        place = Place.objects.get(id=self.data.get('place'))
        cells = MatrixCellPlace.objects.filter(variant=variant.id, place=place)
        cells = cells.annotate(cell_code=F('cell__cellcode'), value=F('minutes'))
        return cells


class ReachabilityCell(ModeVariantMixin, ComputeIndicator):
    '''Wegezeit zwischen ausgewähltem Wohnstandort (= Rasterzelle) und allen
    Einrichtungen'''
    title = 'Erreichbarkeit Wohnstandort'
    description = ('Wegezeit zwischen ausgewähltem Wohnstandort (= Rasterzelle) '
                   'und allen Einrichtungen')
    result_serializer = ResultSerializer.PLACE

    def compute(self):
        mode = self.data.get('mode', Mode.WALK)
        scenario_id = self.data.get('scenario')
        variant = self.get_mode_variant(mode, scenario_id)

        cell_code = self.data.get('cell_code')
        places = MatrixCellPlace.objects.filter(variant=variant,
                                                cell__cellcode=cell_code)
        places = places.values('place_id', 'minutes')\
            .annotate(id=F('place_id'), value=F('minutes'))
        return places


class ReachabilityNextPlace(ModeVariantMixin, ComputeIndicator):
    '''Wegezeit zwischen allen Wohnstandorten (= Rasterzellen)
    und der jeweils nächstgelegenen Einrichtung
    '''
    title = 'Erreichbarkeit nächste Einrichtung'
    description = ('Wegezeit zwischen allen Wohnstandorten (= Rasterzellen) '
                   'und der jeweils nächstgelegenen Einrichtung ')
    result_serializer = ResultSerializer.RASTER

    def compute(self):
        mode = self.data.get('mode', Mode.WALK)
        service_ids = self.data.get('services')
        year = self.data.get('year')
        scenario_id = self.data.get('scenario')
        variant = self.get_mode_variant(mode, scenario_id)

        capacities = Capacity.objects.all()
        capacities = Capacity.filter_queryset(capacities,
                                              service_ids=service_ids,
                                              scenario_id=scenario_id,
                                              year=year,
                                              )
        # only those with capacity - value > 0
        capacities = capacities.filter(capacity__gt=0)

        place_ids = capacities.distinct('place_id').values_list('place_id', flat=True)
        mcp = MatrixCellPlace.objects.filter(variant=variant,
                                             place__in=place_ids)
        cells = mcp.values('cell_id')\
            .annotate(value=Min('minutes'))\
            .annotate(cell_code=F('cell__cellcode'))
        return cells

