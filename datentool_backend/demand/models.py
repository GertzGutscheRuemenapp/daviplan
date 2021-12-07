from django.db import models
from datentool_backend.base import NamedModel
from datentool_backend.population.models import (AgeGroup, Year)

class DemandRateSet(NamedModel, models.Model):
    """ set of demand """
    name = models.TextField()
    is_default = models.BooleanField()


class DemandRate(models.Model):
    """ demand rate """
    year = models.ForeignKey(Year, on_delete=models.RESTRICT)
    age_group = models.ForeignKey(AgeGroup, on_delete=models.RESTRICT)
    demand_rate_set =  models.ForeignKey(DemandRateSet, on_delete=models.RESTRICT)
