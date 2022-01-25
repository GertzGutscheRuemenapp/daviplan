from abc import ABCMeta
from typing import Callable, Dict
from django.db.models import OuterRef, Subquery, Count, IntegerField
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from sql_util.utils import Exists

from datentool_backend.infrastructure.models import FieldTypes
from .models import IndicatorType
from datentool_backend.area.models import Area
from datentool_backend.infrastructure.models import Place, Capacity



class ComputeIndicator(metaclass=ABCMeta):

    label: str = None
    description: str = None
    parameters: Dict[str, str] = {}

    def __init__(self,
                 query_params: Dict[str, str]
                 ):
        self.query_params = query_params

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
        area_level_id = self.query_params.get('area_level')
        service_id = self.query_params.get('service')
        year = self.query_params.get('year', 0)
        scenario_id = self.query_params.get('scenario')

        qs = Area.objects.filter(area_level=area_level_id)

        name_attr = 'name'
        qs = qs.annotate(name=KeyTextTransform(name_attr, 'attributes'))


        capacities = Capacity.objects.all()
        capacities = Capacity.filter_queryset(capacities,
                                              service_id=service_id,
                                              scenario_id=scenario_id,
                                              year=year,
                                              )
        # only those with capacity - value > 0
        capacities = capacities.filter(capacity__gt=0)

        places = Place.objects.all()
        places_with_capacity = places.annotate(
            has_capacity=Exists(capacities.filter(place=OuterRef('pk'))))\
            .filter(has_capacity=True)

        places_in_area = places_with_capacity\
            .filter(geom__intersects=OuterRef('geom'))\
            .annotate(area_id=OuterRef('id'))\
            .values('area_id')\
            .annotate(n_places=Count('*'))\
            .values('n_places')
        qs = qs.annotate(
            value=Subquery(
                places_in_area, output_field=IntegerField()
            )
        )
        return qs


@register_indicator_class()
class SumCapacity(ComputeIndicator):
    label = 'SumCap'
    description = 'Sum Capacity of Locations per Area'

    def compute(self):
        """"""


