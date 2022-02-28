from abc import ABCMeta, abstractmethod
from typing import Callable, Dict# Literal
from django.http.request import QueryDict
import enum

from datentool_backend.infrastructure.models import FieldTypes
from datentool_backend.user.models import Service


class ComputeIndicator(metaclass=ABCMeta):
    label: str = None
    parameters: Dict[str, FieldTypes] = {}

    @abstractmethod
    def compute(self, query_params: QueryDict):
        """compute the indicator"""

    def __str__(self):
        return f'{self.__class__.__name__}: {self.label}'


class CapacityRequirement(enum.IntEnum):
    required = 1
    not_required = 2
    independent = 3


class AssessmentIndicator(ComputeIndicator):
    registered: Dict[int, ComputeIndicator] = {}
    description: str = None
    title: str = None
    detailed_title: str = None
    capacity_required: int = CapacityRequirement.independent # Literal[1, 2, 3]

    def __init__(self, service: Service):
        super().__init__()
        self.service = service

    @property
    def id(self) -> int:
        for id, indicator_class in self.registered.items():
            if isinstance(self, indicator_class):
                return id
        return -1

    @property
    @abstractmethod
    def detailed_title(self) -> str:
        """computed title"""
        return ''


class AreaAssessmentIndicator(AssessmentIndicator):
    """compute return type Area"""


class RasterAssessmentIndicator(AssessmentIndicator):
    """compute return type RasterCell"""


class PlaceAssessmentIndicator(AssessmentIndicator):
    """compute return type Place"""


def register_indicator() -> Callable:
    """register the indicator with the ComputeIndicators"""

    def wrapper(wrapped_class: AssessmentIndicator) -> Callable:
        _id = max(AssessmentIndicator.registered.keys() or [0]) + 1
        AssessmentIndicator.registered[_id] = wrapped_class
        return wrapped_class
    return wrapper
