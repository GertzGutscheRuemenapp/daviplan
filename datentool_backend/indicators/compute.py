from abc import ABCMeta, abstractmethod
from typing import Callable, Dict
from django.db.models import OuterRef, Subquery, Count, IntegerField, Sum, FloatField
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from sql_util.utils import Exists, SubquerySum

from datentool_backend.infrastructure.models import FieldTypes
from .models import IndicatorType
from datentool_backend.area.models import Area
from datentool_backend.infrastructure.models import Place, Capacity



class ComputeIndicator(metaclass=ABCMeta):

    label: str = None
    description: str = None
    parameters: Dict[str, FieldTypes] = {}

    def __init__(self,
                 query_params: Dict[str, str]
                 ):
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


class ComputeAreaIndicator(ComputeIndicator, metaclass=ABCMeta):

    def compute(self):
        """"""
        area_level_id = self.query_params.get('area_level')
        service_id = self.query_params.get('service')
        year = self.query_params.get('year', 0)
        scenario_id = self.query_params.get('scenario')

        areas = Area.objects.filter(area_level=area_level_id)

        name_attr = 'gen'
        areas = areas.annotate(name=KeyTextTransform(name_attr, 'attributes'))


        capacities = Capacity.objects.all()
        capacities = Capacity.filter_queryset(capacities,
                                              service_id=service_id,
                                              scenario_id=scenario_id,
                                              year=year,
                                              )
        # only those with capacity - value > 0
        capacities = capacities.filter(capacity__gt=0)
        places = Place.objects.all()
        areas = self.aggregate_places(places, capacities, areas)
        return areas

    @abstractmethod
    def aggregate_places(self,
                         places: Place,
                         capacities: Capacity,
                         areas: Area) -> Area:
        """annotate the areas-queryset with a value-Field, that is an aggregate
        of places and capacities"""


@register_indicator_class()
class NumberOfLocations(ComputeAreaIndicator):
    label = 'NumLocations'
    description = 'Number of Locations per Area'

    def aggregate_places(self,
                         places: Place,
                         capacities: Capacity,
                         areas: Area) -> Area:
        """Counts the number of places per area"""
        places_with_capacity = places.annotate(
            has_capacity=Exists(capacities.filter(place=OuterRef('pk'))))\
            .filter(has_capacity=True)

        places_with_area = places_with_capacity\
            .filter(geom__intersects=OuterRef('geom'))\
            .annotate(area_id=OuterRef('id'))\
            .values('area_id')

        places_in_area = places_with_area\
            .annotate(n_places=Count('*'))\
            .values('n_places')
        areas = areas.annotate(
            value=Subquery(places_in_area, output_field=IntegerField())
        )
        return areas


@register_indicator_class()
class TotalCapacityInArea(ComputeAreaIndicator):
    label = 'Total Capacity'
    description = 'Total Capacity per Area'

    def aggregate_places(self,
                         places: Place,
                         capacities: Capacity,
                         areas: Area) -> Area:
        """Sums up the capacity per area"""
        places_with_capacity = places.annotate(
            service_cap=capacities
            .filter(place=OuterRef('pk'))
            .values('capacity'))

        places_with_area = places_with_capacity\
            .filter(geom__intersects=OuterRef('geom'))\
            .annotate(area_id=OuterRef('id'))\
            .values('area_id')

        places_in_area = places_with_area\
            .annotate(total_capacity=Sum('service_cap'))\
            .values('total_capacity')

        areas = areas.annotate(
            value=Subquery(places_in_area)
        )
        return areas

