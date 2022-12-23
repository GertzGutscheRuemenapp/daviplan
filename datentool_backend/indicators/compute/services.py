from abc import ABCMeta, abstractmethod
from django.db.models import OuterRef, Subquery, Count, IntegerField, Sum
from django.db.models.functions import Coalesce
from sql_util.utils import Exists

from datentool_backend.indicators.compute.base import ComputeIndicator, ResultSerializer
from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.places.models import Place, Capacity


class ComputeAreaIndicator(ComputeIndicator, metaclass=ABCMeta):
    result_serializer = ResultSerializer.AREA

    def compute(self):
        """"""
        area_level_id = self.data.get('area_level')
        service_id = self.data.get('service')
        year = self.data.get('year', 0)
        scenario_id = self.data.get('scenario')

        area_level = AreaLevel.objects.get(id=area_level_id)
        areas = Area.label_annotated_qs(area_level=area_level)

        capacities = Capacity.objects.all()
        capacities = Capacity.filter_queryset(capacities,
                                              service_ids=[service_id],
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


class NumberOfLocations(ComputeAreaIndicator):
    title = 'NumLocations'
    description = 'Number of Locations per Area'
    representation = 'colorramp'
    colormap_name = 'Blues'

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


class TotalCapacityInArea(ComputeAreaIndicator):
    title = 'Total Capacity'
    description = 'Total Capacity per Area'
    representation = 'colorramp'
    colormap_name = 'Blues'

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
