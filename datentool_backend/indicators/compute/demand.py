from django.db.models import OuterRef, Subquery, Sum
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import F

from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.population.models import RasterCellPopulationAgeGender, AreaCell
from .base import ComputeIndicator, register_indicator_class
from datentool_backend.indicators.compute.population import PopulationIndicatorMixin
from datentool_backend.demand.models import DemandRateSet, DemandRate
from datentool_backend.infrastructure.models import ScenarioService
from datentool_backend.user.models import Year


@register_indicator_class()
class DemandAreaIndicator(PopulationIndicatorMixin,
                          ComputeIndicator):
    label = 'Demand for Service By Area'
    description = 'Total Demand for Service per Area'
    category = 'Population Services'
    userdefined = False

    def compute(self):
        """"""
        area_level_id = self.query_params.get('area_level')
        areas = self.get_areas(area_level_id=area_level_id)
        rcpop = self.get_population()
        acells = AreaCell.objects.filter(area__area_level_id=area_level_id)

        demand_rates = self.get_demand_rates()

        sq = demand_rates\
            .filter(age_group=OuterRef('age_group'), gender=OuterRef('gender'))\
            .annotate(demandrate=F('value'))\
            .values('demandrate')[:1]

        rcpop_with_dr = rcpop.annotate(demandrate=Subquery(sq))

        # sum up the rastercell-population * demand to areas taking the share_area_of_cell
        # into account

        sq = rcpop_with_dr.filter(cell=OuterRef('cell__cell'))\
            .annotate(area_id=OuterRef('area_id'),
                      share_area_of_cell=OuterRef('share_area_of_cell'))\
            .values('area_id')\
            .annotate(sum_pop=Sum(F('value') * F('demandrate') * F('share_area_of_cell')))\
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

    def get_demand_rates(self) -> DemandRate:
        """get the demand rates for a scenario, year and service"""
        scenario = self.query_params.get('scenario')
        service = self.query_params.get('service')
        try:
            scenario_service = ScenarioService.objects.get(scenario=scenario,
                                                           service_id=service)
            drs = scenario_service.demandrateset
        except ScenarioService.DoesNotExist:
            drs = DemandRateSet.objects.get(service=service, is_default=True)

        year = self.query_params.get('year')
        if year:
            year = Year.objects.get(year=year)
        else:
            year = Year.objects.get(is_default=True)

        demand_rates = drs.demandrate_set.filter(year=year)
        return demand_rates
