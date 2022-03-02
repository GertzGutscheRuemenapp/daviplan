from abc import ABCMeta, abstractmethod
from typing import Callable, Dict, List
from django.http.request import QueryDict
from enum import Enum

from datentool_backend.infrastructure.models import FieldTypes
from datentool_backend.user.models import Service
from datentool_backend.indicators.serializers import (
    IndicatorAreaResultSerializer, IndicatorRasterResultSerializer,
    IndicatorPlaceResultSerializer)


class ComputeIndicator(metaclass=ABCMeta):
    label: str = None
    parameters: Dict[str, FieldTypes] = {}

    def __init__(self, query_params: QueryDict = None):
        self.query_params = query_params

    @abstractmethod
    def compute(self):
        """compute the indicator"""

    def __str__(self):
        return f'{self.__class__.__name__}: {self.label}'


class ResultSerializer(Enum):
    AREA = IndicatorAreaResultSerializer
    PLACE = IndicatorPlaceResultSerializer
    RASTER = IndicatorRasterResultSerializer


class AssessmentIndicator(ComputeIndicator):
    registered: Dict[str, 'AssessmentIndicator'] = {}
    title: str = None
    capacity_required: bool = False
    result_serializer: ResultSerializer = None

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
