from abc import ABCMeta, abstractmethod
from typing import Callable, Dict
from django.http.request import QueryDict
from django.db.models import OuterRef, Subquery, Count, IntegerField, Sum, FloatField
from django.db.models.functions import Coalesce
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import F
from sql_util.utils import Exists

from datentool_backend.infrastructure.models import FieldTypes
from .models import IndicatorType
from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.infrastructure.models import Place, Capacity
from datentool_backend.population.models import RasterCellPopulationAgeGender, AreaCell



class ComputeIndicator(metaclass=ABCMeta):

    label: str = None
    description: str = None
    parameters: Dict[str, FieldTypes] = {}
    category: str = 'General'

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
    category = 'Infrastructure Services'

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
    category = 'Infrastructure Services'

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
    category = 'Population Services'

    def compute(self):
        """"""
        area_level_id = self.query_params.get('area_level')
        area_level = AreaLevel.objects.get(pk=area_level_id)

        area_filter = {}
        areas = self.query_params.getlist('area')
        if areas:
            area_filter['id__in'] = areas

        area_set = area_level.area_set.filter(**area_filter)
        area_set = area_set.annotate(
            label=KeyTextTransform(area_level.label_field, 'attributes'))

        acells = AreaCell.objects.filter(area__area_level_id=area_level_id)

        filter_params = {}
        year = self.query_params.get('year')
        if year:
            filter_params['year'] = year

        genders = self.query_params.getlist('gender')
        if genders:
            filter_params['gender__in'] = genders

        age_groups = self.query_params.getlist('age_group')
        if age_groups:
            filter_params['age_group__in'] = age_groups

        # filter the rastercell-population by year, age_group and gender, if given
        population = RasterCellPopulationAgeGender.objects.filter(**filter_params)

        # sum up the rastercell-population to areas taking the share_area_of_cell
        # into account

        sq = population.filter(cell=OuterRef('cell__cell'))\
            .annotate(area_id=OuterRef('area_id'),
                      share_area_of_cell=OuterRef('share_area_of_cell'))\
            .values('area_id')\
            .annotate(sum_pop=Sum(F('value') * F('share_area_of_cell')))\
            .values('sum_pop')

        # sum up by area
        aa = acells.annotate(sum_pop=Subquery(sq))\
            .values('area_id')\
            .annotate(sum_pop=Sum('sum_pop'))

        # annotate areas with the results
        sq = aa.filter(area_id=OuterRef('pk'))\
            .values('sum_pop')
        areas_with_pop = area_set.annotate(value=Subquery(sq))

        return areas_with_pop


@register_indicator_class()
class ComputePopulationDetailAreaIndicator(ComputeIndicator):
    label = 'Population By Gender, AgeGroup and Year'
    description = 'Population by Gender, Agegroup and Year for one or several areas'
    category = 'Population Services'

    def compute(self):
        """"""

        # filter areas
        area_filter = {}
        areas = self.query_params.getlist('area')
        if areas:
            area_filter['id__in'] = areas

        areas = Area.objects.filter(**area_filter)
        acells = AreaCell.objects.filter(area__in=areas)

        #  other filters
        filter_params = {}
        year = self.query_params.get('year')
        if year:
            filter_params['disaggraster__raster__year'] = year

        genders = self.query_params.getlist('gender')
        if genders:
            filter_params['gender__in'] = genders

        age_groups = self.query_params.getlist('age_group')
        if age_groups:
            filter_params['age_group__in'] = age_groups


        # filter the rastercell-population by year, age_group and gender, if given
        rasterpop = RasterCellPopulationAgeGender.objects.filter(**filter_params)

        # sum up the rastercell-population of the areas to rastercells taking the share_area_of_cell
        # into account
        sq = acells.filter(cell__cell=OuterRef('cell'))\
            .annotate(pop=OuterRef('value') * F('share_area_of_cell'),
                      year=OuterRef('year'),
                      gender=OuterRef('gender_id'),
                      agegroup=OuterRef('age_group_id'))\
            .values('cell', 'year', 'gender', 'agegroup')\
            .annotate(sum_pop=Sum('pop'))

        #  and sum up all rastercells in the selected area(s),
        #  grouped by ayer, gender and agegroup
        qs = rasterpop.annotate(sum_pop=Subquery(sq.values('sum_pop')))
        qs2 = qs\
            .values('year', 'gender_id', 'age_group_id')\
            .annotate(value=Sum('sum_pop'),
                      gender=F('gender_id'),
                      agegroup=F('age_group_id')
                      )
        #  return only these columns
        qs3 = qs2.values('year', 'gender', 'agegroup', 'value')
        return qs3

