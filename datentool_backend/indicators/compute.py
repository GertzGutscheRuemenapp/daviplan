from abc import ABCMeta
from typing import Callable, Dict
from django.db import models
from collections import OrderedDict
from datentool_backend.base import (NamedModel,
                                    JsonAttributes,
                                    )
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE

from datentool_backend.infrastructure.models import FieldType, FieldTypes



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


class IndicatorType(NamedModel, models.Model):
    _indicator_classes: Dict[str, ComputeIndicator] = {}

    name = models.TextField(unique=True)
    classname = models.TextField(unique=True)
    description = models.TextField()
    parameters = models.ManyToManyField(FieldType, through='IndicatorTypeFields')


    @classmethod
    def _check_indicators(cls):
        """check if all Indicators are in the database and add them, if not"""
        for classname, indicator_class in cls._indicator_classes.items():
            obj, created = IndicatorType.objects.get_or_create(classname=classname)
            obj.name = indicator_class.label
            obj.description = indicator_class.description
            obj.save()
            for field_name, field_descr in indicator_class.parameters.items():
                field_type, created = FieldType.objects.get_or_create(
                    field_type=field_descr.value, name=field_name)
                itf, created= IndicatorTypeFields.objects.get_or_create(
                    indicator_type=obj, field_type=field_type)
                itf.label = field_name
                itf.save()
        deleted_types = IndicatorType.objects.exclude(classname__in=cls._indicator_classes.keys())
        deleted_types.delete()

    @classmethod
    def _add_indicator_class(cls, indicator_class):
        cls._indicator_classes[indicator_class.__name__] = indicator_class


class IndicatorTypeFields(models.Model):
    indicator_type = models.ForeignKey(IndicatorType, on_delete=PROTECT_CASCADE)
    field_type = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    label = models.TextField()


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


