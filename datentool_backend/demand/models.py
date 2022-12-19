from django.db import models, transaction

from datentool_backend.base import NamedModel
from datentool_backend.infrastructure.models import Service
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
                    is_default=True, service=self.service
                    ).update(is_default=False)
        # on creation -> look if there is already a default set for the service,
        # else set this as default (so there is always a default one)
        elif self.pk is None:
            try:
                DemandRateSet.objects.get(is_default=True, service=self.service)
            except DemandRateSet.DoesNotExist:
                self.is_default = True
        return super().save(*args, **kwargs)

    def delete(self, **kwargs):
        # deleting set marked as default for the service -> mark another one
        # of the same service (so there always is one default set if there are
        # any at all)
        if self.is_default:
            new_default = DemandRateSet.objects.filter(
                service=self.service).exclude(id=self.id).first()
            if new_default:
                new_default.is_default = True
                new_default.save()
        return super().delete(**kwargs)


class DemandRate(models.Model):
    """ demand rate """
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    age_group = models.ForeignKey(AgeGroup, on_delete=models.CASCADE)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE)
    demand_rate_set = models.ForeignKey(DemandRateSet, on_delete=models.CASCADE)
    value = models.FloatField(null=True)