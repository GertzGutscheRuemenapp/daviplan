from django.db.models import OuterRef, Subquery, Sum
from django.db.models import F

from .base import ComputeIndicator, register_indicator_class
from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.population.models import RasterCellPopulationAgeGender, AreaCell
from datentool_backend.infrastructure.models import Scenario


class PopulationIndicatorMixin:

    def get_population(self) -> RasterCellPopulationAgeGender:
        """get the population per area in the scenario"""
        scenario = self.query_params.get('scenario')
        if scenario:
            prognosis = Scenario.objects.get(pk=scenario).prognosis_id
        else:
            prognosis = self.query_params.get('prognosis')
        filter_params = {'population__prognosis': prognosis,}
        year = self.query_params.get('year')
        if year:
            filter_params['population__year__year'] = year

        genders = self.query_params.getlist('gender')
        if genders:
            filter_params['gender__in'] = genders

        age_groups = self.query_params.getlist('age_group')
        if age_groups:
            filter_params['age_group__in'] = age_groups

        # filter the rastercell-population by year, age_group and gender, if given
        population = RasterCellPopulationAgeGender.objects.filter(**filter_params)
        return population

    def get_areas(self, area_level_id: int=None) -> Area:
        """get the relevant areas"""
        # filter areas
        area_filter = {}
        if area_level_id:
            area_filter['area_level_id'] = area_level_id
        areas = self.query_params.getlist('area')
        if areas:
            area_filter['id__in'] = areas

        areas = Area.objects.filter(**area_filter)
        return areas


@register_indicator_class()
class ComputePopulationAreaIndicator(PopulationIndicatorMixin,
                                     ComputeIndicator):
    label = 'Population By Area'
    description = 'Total Population per Area'
    category = 'Population Services'
    userdefined = False

    def compute(self):
        """"""
        area_level_id = self.query_params.get('area_level')
        areas = self.get_areas(area_level_id=area_level_id)
        acells = AreaCell.objects.filter(area__area_level_id=area_level_id)
        population = self.get_population()

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
        areas_with_pop = areas.annotate(value=Subquery(sq))

        return areas_with_pop


@register_indicator_class()
class ComputePopulationDetailAreaIndicator(PopulationIndicatorMixin,
                                           ComputeIndicator):
    label = 'Population By Gender, AgeGroup and Year'
    description = 'Population by Gender, Agegroup and Year for one or several areas'
    category = 'Population Services'
    userdefined = False

    def compute(self):
        """"""

        areas = self.get_areas()
        acells = AreaCell.objects.filter(area__in=areas)

        # filter the rastercell-population by year, age_group and gender, if given
        rasterpop = self.get_population()

        # sum up the rastercell-population of the areas to rastercells taking the share_area_of_cell
        # into account
        sq = acells.filter(cell__cell=OuterRef('cell'))\
            .annotate(pop=OuterRef('value') * F('share_area_of_cell'),
                      year=OuterRef('population__year'),
                      gender=OuterRef('gender_id'),
                      agegroup=OuterRef('age_group_id'))\
            .values('cell', 'year', 'gender', 'agegroup')\
            .annotate(sum_pop=Sum('pop'))

        #  and sum up all rastercells in the selected area(s),
        #  grouped by ayer, gender and agegroup
        qs = rasterpop.annotate(sum_pop=Subquery(sq.values('sum_pop')))
        qs2 = qs\
            .values('population__year', 'gender_id', 'age_group_id')\
            .annotate(value=Sum('sum_pop'),
                      gender=F('gender_id'),
                      agegroup=F('age_group_id'),
                      year=F('population__year__year'),
                      )
        #  return only these columns
        qs3 = qs2.values('year', 'gender', 'agegroup', 'value')
        return qs3


