from abc import ABCMeta, abstractmethod
from typing import Callable, Dict, List, Tuple
from django.http.request import QueryDict
from enum import Enum

from datentool_backend.user.models import Service
from datentool_backend.indicators.serializers import (
    IndicatorAreaResultSerializer, IndicatorRasterResultSerializer,
    IndicatorPlaceResultSerializer)


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


class ComputeIndicator(metaclass=ABCMeta):
    title: List[Tuple] = None

    def __init__(self, query_params: QueryDict = None):
        self.query_params = query_params

    @abstractmethod
    def compute(self):
        """compute the indicator"""

    def __str__(self):
        return f'{self.__class__.__name__}: {self.title}'


class ResultSerializer(Enum):
    AREA = IndicatorAreaResultSerializer
    PLACE = IndicatorPlaceResultSerializer
    RASTER = IndicatorRasterResultSerializer


class AssessmentIndicator(ComputeIndicator):
    registered: Dict[str, 'AssessmentIndicator'] = {}
    capacity_required: bool = False
    result_serializer: ResultSerializer = None
    params: List[IndicatorParameter] = []

    def __init__(self, service: Service, query_params: QueryDict = None):
        super().__init__(query_params)
        self.service = service

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    @property
    @abstractmethod
    def description(self) -> str:
        """computed title"""
        return ''

    def serialize(self, queryset):
        if not self.result_serializer:
            raise Exception('no serializer defined')
        serializer = self.result_serializer.value
        return serializer(queryset, many=True).data


class AreaAssessmentIndicator(AssessmentIndicator):
    """compute return type Area"""
    result_serializer = ResultSerializer.AREA


class RasterAssessmentIndicator(AssessmentIndicator):
    """compute return type RasterCell"""
    result_serializer = ResultSerializer.RASTER


class PlaceAssessmentIndicator(AssessmentIndicator):
    """compute return type Place"""
    result_serializer = ResultSerializer.PLACE


def register_indicator() -> Callable:
    """register the indicator with the ComputeIndicators"""

    def wrapper(wrapped_class: AssessmentIndicator) -> Callable:
        name = wrapped_class.__name__.lower()
        AssessmentIndicator.registered[name] = wrapped_class
        return wrapped_class
    return wrapper
