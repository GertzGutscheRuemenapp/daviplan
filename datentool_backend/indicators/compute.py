from abc import ABCMeta
from typing import Callable, Dict

from datentool_backend.infrastructure.models import FieldTypes
from .models import IndicatorType


class ComputeIndicator(metaclass=ABCMeta):

    label: str = None
    description: str = None
    parameters: Dict[str, str] = {}

    def __init__(self,
                 service: int,
                 area_level: int,
                 scenario: int = None,
                 year: int = None,
                 ):
        self.service = service
        self.area_level = area_level
        self.scenario = scenario
        self.year = year

    def compute(self):
        """compute the indicator"""
        return NotImplemented

    def __str__(self):
        return f'{self.__name__}: {self.code}'


def register_indicator_class() -> Callable:
    """register the indicator with the ComputeIndicators"""

    def wrapper(wrapped_class: ComputeIndicator) -> Callable:
        IndicatorType._add_indicator_class(wrapped_class)
        return wrapped_class
    return wrapper


@register_indicator_class()
class TestIndicator(ComputeIndicator):
    label = 'TE'
    description = 'Random Indicator'
    parameters = {'Max_Value': FieldTypes.NUMBER, 'TextField': FieldTypes.STRING, }

    def compute(self):
        """"""


@register_indicator_class()
class NumberOfLocations(ComputeIndicator):
    label = 'NumLocations'
    description = 'Number of Locations per Area'

    def compute(self):
        """"""


@register_indicator_class()
class SumCapacity(ComputeIndicator):
    label = 'SumCap'
    description = 'Sum Capacity of Locations per Area'

    def compute(self):
        """"""


