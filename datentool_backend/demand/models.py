from django.db import models, transaction

from datentool_backend.base import NamedModel
from datentool_backend.infrastructure.models.infrastructures import Service
from datentool_backend.population.models import Year, AgeGroup, Gender
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.base import NamedModel, DatentoolModelMixin


class DemandRateSet(DatentoolModelMixin, NamedModel, models.Model):
    """ set of demand """
    name = models.TextField()
    is_default = models.BooleanField(default=False)
    service = models.ForeignKey(Service, on_delete=PROTECT_CASCADE)
    description = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        # only one default per service
        if self.is_default:
            with transaction.atomic():
                DemandRateSet.objects.filter(
                    is_default=True, service=self.service).update(is_default=False)
        return super().save(*args, **kwargs)


class DemandRate(models.Model):
    """ demand rate """
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    age_group = models.ForeignKey(AgeGroup, on_delete=models.CASCADE)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE)
    demand_rate_set = models.ForeignKey(DemandRateSet, on_delete=models.CASCADE)
    value = models.FloatField(null=True)