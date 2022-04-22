from abc import ABCMeta, abstractmethod
from typing import Callable, Dict, List, Tuple
from enum import Enum

from django.http.request import QueryDict

from datentool_backend.modes.models import Mode
from datentool_backend.infrastructure.models.infrastructures import Service
from datentool_backend.indicators.serializers import (
    IndicatorAreaResultSerializer,
    IndicatorRasterResultSerializer,
    IndicatorPlaceResultSerializer,
    IndicatorPopulationSerializer)


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


#class ColorScheme():
    #def __init__(self, scheme: Union[str, List[str]], n_bins: int = 0):
        #self.scheme = scheme
        #self.n_bins = n_bins
        #self.mid_value


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
        return serializer(queryset, many=True).data


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


def register_indicator() -> Callable:
    """register the indicator with the ComputeIndicators"""

    def wrapper(wrapped_class: ServiceIndicator) -> Callable:
        name = wrapped_class.__name__.lower()
        ServiceIndicator.registered[name] = wrapped_class
        return wrapped_class
    return wrapper
