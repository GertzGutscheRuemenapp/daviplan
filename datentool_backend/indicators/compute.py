from abc import ABCMeta, abstractmethod
from typing import Callable, Dict
from django.http.request import QueryDict
from django.db.models import OuterRef, Subquery, Count, IntegerField, Sum
from django.db.models.functions import Coalesce
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from sql_util.utils import Exists

from datentool_backend.infrastructure.models import FieldTypes
from .models import IndicatorType
from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.infrastructure.models import Place, Capacity
from datentool_backend.population.models import RasterCellPopulationAgeGender



class ComputeIndicator(metaclass=ABCMeta):

    label: str = None
    description: str = None
    parameters: Dict[str, FieldTypes] = {}

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


class ComputeAreaIndicator(ComputeIndicator, metaclass=ABCMeta):

    def compute(self):
        """"""
        area_level_id = self.query_params.get('area_level')
        service_ids = self.query_params.getlist('service')
        year = self.query_params.get('year', 0)
        scenario_id = self.query_params.get('scenario')

        area_level = AreaLevel.objects.get(pk=area_level_id)
        areas = area_level.area_set.all()

        areas = areas.annotate(
            label=KeyTextTransform(area_level.label_field, 'attributes'))


        capacities = Capacity.objects.all()
        capacities = Capacity.filter_queryset(capacities,
                                              service_ids=service_ids,
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

        # sum up the capacity per place over all services
        places_with_capacity = places.annotate(
            service_cap=capacities
            .filter(place=OuterRef('pk'))\
            .values('place')\
            .annotate(place_capacity=Sum('capacity'))\
            .values('place_capacity'))

        # intersect with areas and annotate area_id
        places_with_area = places_with_capacity\
            .filter(geom__intersects=OuterRef('geom'))\
            .annotate(area_id=OuterRef('id'))\
                    .values('area_id')

        # group by area_id and sum the capacity of the places
        # if no place in an area, set to 0 instead of NULL with Coalesce
        sq1 = places_with_area\
            .annotate(total_capacity=Coalesce(Sum('service_cap'), 0.0))\
            .values('total_capacity')

        # write value calculated in subquery to area-queryset
        areas_with_capacities = areas\
            .annotate(value=Subquery(sq1))

        return areas_with_capacities


@register_indicator_class()
class ComputePopulationAreaIndicator(ComputeIndicator):
    label = 'Population By Area'
    description = 'Total Population per Area'

    def compute(self):
        """"""
        area_level_id = self.query_params.get('area_level')
        year = self.query_params.get('year', 0)
        scenario_id = self.query_params.get('scenario')

        area_level = AreaLevel.objects.get(pk=area_level_id)
        areas = area_level.area_set.all()

        areas = areas.annotate(
            label=KeyTextTransform(area_level.label_field, 'attributes'))


        population = RasterCellPopulationAgeGender.objects.all()

        areas = self.aggregate_population(population, areas)
        return areas

    def aggregate_population(self,
                             population: RasterCellPopulationAgeGender,
                             areas: Area) -> Area:
        """"""
