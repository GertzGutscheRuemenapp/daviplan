from abc import ABCMeta, abstractmethod
from typing import Callable, Dict
from django.http.request import QueryDict

from datentool_backend.infrastructure.models import FieldTypes
from datentool_backend.indicators.models import IndicatorType


class ComputeIndicator(metaclass=ABCMeta):

    label: str = None
    description: str = None
    parameters: Dict[str, FieldTypes] = {}
    category: str = 'General'
    userdefined: bool = True

    def __init__(self, query_params: QueryDict):
        self.query_params = query_params

    @abstractmethod
    def compute(self):
        """compute the indicator"""

    def __str__(self):
        return f'{self.__class__.__name__}: {self.label}'


def register_indicator_class() -> Callable:
    """register the indicator with the ComputeIndicators"""

    def wrapper(wrapped_class: ComputeIndicator) -> Callable:
        IndicatorType._add_indicator_class(wrapped_class)
        return wrapped_class
    return wrapper
