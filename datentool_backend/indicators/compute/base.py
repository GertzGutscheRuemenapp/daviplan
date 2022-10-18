from abc import ABCMeta, abstractmethod
from typing import Callable, Dict, List, Tuple
from enum import Enum
import numpy as np

from django.http.request import QueryDict
from django.db.models import OuterRef, F
from sql_util.utils import Exists
from datentool_backend.infrastructure.models.places import Place, Capacity

from datentool_backend.modes.models import Mode, ModeVariant
from datentool_backend.infrastructure.models.infrastructures import Service
from datentool_backend.indicators.serializers import (
    IndicatorAreaResultSerializer,
    IndicatorRasterResultSerializer,
    IndicatorPlaceResultSerializer,
    IndicatorPopulationSerializer)
from datentool_backend.indicators.legend import get_colors, get_percentiles


class IndicatorParameter:
    type: str = 'string'
    def __init__(self, name: str, title: str = None):
        self.name = name
        self.title = title or name

    def serialize(self):
        return {
            'name': self.name,
            'type': self.type,
            'title':  self.title
        }


class IndicatorNumberParameter(IndicatorParameter):
    type: str = 'number'
    def __init__(self, name: str, title: str = None,
                 min: int = None, max: int = None,
                 integer_only: bool = True):
        super().__init__(name, title=title)
        self.min = min
        self.max = max

    def serialize(self):
        ret = super() .serialize()
        ret['min'] = self.min
        ret['max'] = self.max
        return ret


class IndicatorChoiceParameter(IndicatorParameter):
    type: str = 'choice'
    def __init__(self, name: str, choices: List[Tuple],
                 title: str = None):
        super().__init__(name, title=title)
        self.choices = choices

    def serialize(self):
        ret = super() .serialize()
        ret['choices'] = self.choices
        return ret


class ModeParameter(IndicatorChoiceParameter):
    name = 'mode'
    title = 'Verkehrsmittel'
    choices = Mode.choices
    def __init__(self):
        super().__init__(self.name, self.choices, title=self.title)


class ResultSerializer(Enum):
    AREA = IndicatorAreaResultSerializer
    PLACE = IndicatorPlaceResultSerializer
    RASTER = IndicatorRasterResultSerializer
    POP = IndicatorPopulationSerializer


class ComputeIndicator(metaclass=ABCMeta):
    title: List[Tuple] = None
    result_serializer: ResultSerializer = None
    params: List[IndicatorParameter] = []
    description: str = ''

    def __init__(self, data: QueryDict = None):
        self.data = data

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    @abstractmethod
    def compute(self):
        """compute the indicator"""

    def __str__(self):
        return f'{self.__class__.__name__}: {self.title}'

    def serialize(self, queryset):
        if not self.result_serializer:
            raise Exception('no serializer defined')
        serializer = self.result_serializer.value
        values = serializer(queryset, many=True).data
        legend = self.get_legend(values)
        return {'legend': legend,
                'values': values, }

    def get_legend(self, values):
        """get the legend based on the values"""
        if getattr(self, 'representation', None) != 'colorramp':
            return {}

        legend_entries = []
        try:
            bins = self.bins
        except AttributeError:
            try:
                bins_my_mode = self.bins_by_mode
                mode = self.data['mode']
                mode_variant = ModeVariant.objects.filter(mode=mode).first()
                bins = bins_my_mode[mode_variant.mode]
            except AttributeError:
                percentiles = [0, 10, 20, 40, 60, 80, 90, 100]
                bins = get_percentiles(values, percentiles)

        if bins is None or len(bins) == 0:
            return []
        elif len(bins) == 1:
            value = bins[0]
            if np.isnan(value):
                return {}
            min_values = [value]
            max_values = [value]
        else:
            min_values = bins[:-1]
            max_values = bins[1:]
        n_segments = len(min_values)

        colors = getattr(self, 'colors', None)
        if not colors:
            colors = get_colors(colormap_name=self.colormap_name,
                                n_segments=n_segments)

        for i, color in enumerate(colors):
            entry = dict(min_value=min_values[i],
                         max_value=max_values[i],
                         color=color)
            legend_entries.append(entry)
        return legend_entries



class ServiceIndicator(ComputeIndicator):
    registered: Dict[str, 'AssessmentIndicator'] = {}
    capacity_required: bool = False

    def __init__(self, service: Service, query_params: QueryDict = None):
        super().__init__(query_params)
        self.service = service

    @property
    @abstractmethod
    def description(self) -> str:
        """computed title"""
        return ''

    def get_places_with_capacities(self,
                                   service_id: int,
                                   year: int,
                                   scenario_id: int) -> Place:
        """get places with capacities """

        capacities = Capacity.objects.all()
        capacities = Capacity.filter_queryset(capacities,
                                              service_ids=[service_id],
                                              scenario_id=scenario_id,
                                              year=year,
                                              )
        # only those with capacity - value > 0
        capacities = capacities.filter(capacity__gt=0)

        # filter places with capacity
        places = Place.objects.all()
        places_with_capacity = places.annotate(
            has_capacity=Exists(capacities.filter(place=OuterRef('pk'))))\
            .filter(has_capacity=True)
        return places_with_capacity

def register_indicator() -> Callable:
    """register the indicator with the ComputeIndicators"""

    def wrapper(wrapped_class: ServiceIndicator) -> Callable:
        name = wrapped_class.__name__.lower()
        ServiceIndicator.registered[name] = wrapped_class
        return wrapped_class
    return wrapper
