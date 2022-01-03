from django.db import models
from datentool_backend.base import NamedModel
from datentool_backend.population.models import (AgeGroup, Year)
from datentool_backend.infrastructure.models import (Service)
from datentool_backend.user.models import Scenario


class DemandRateSet(NamedModel, models.Model):
    """ set of demand """
    name = models.TextField()
    is_default = models.BooleanField()
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)


class DemandRate(models.Model):
    """ demand rate """
    year = models.ForeignKey(Year, on_delete=models.RESTRICT)
    age_group = models.ForeignKey(AgeGroup, on_delete=models.RESTRICT)
    demand_rate_set =  models.ForeignKey(DemandRateSet, on_delete=models.RESTRICT)
    value = models.FloatField(null=True)


class ScenarioDemandRate(DemandRate):
    scenario = models.ForeignKey(Scenario, on_delete=models.RESTRICT)