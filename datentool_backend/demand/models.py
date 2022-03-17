from django.db import models, transaction
from django.core.validators import (MinValueValidator, MaxValueValidator)

from datentool_backend.base import NamedModel
from datentool_backend.user.models import (Year, Service)
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.permissions import (CanEditBasedata,
                                                 HasAdminAccessOrReadOnly,
                                                 )

class Gender(DatentoolModelMixin, NamedModel, models.Model):
    """the genders available"""
    name = models.TextField()


class AgeGroup(DatentoolModelMixin, models.Model):
    """an age group in an age classification"""
    from_age = models.IntegerField(validators=[MinValueValidator(0),
                                               MaxValueValidator(127)])
    to_age = models.IntegerField(validators=[MinValueValidator(0),
                                             MaxValueValidator(127)])


class DemandRateSet(DatentoolModelMixin, NamedModel, models.Model):
    """ set of demand """
    name = models.TextField()
    is_default = models.BooleanField(default=False)
    service = models.ForeignKey(Service, on_delete=PROTECT_CASCADE)
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def save(self, *args, **kwargs):
        # only one default per service
        if self.is_default:
            with transaction.atomic():
                DemandRateSet.objects.filter(
                    is_default=True, service=self.service).update(is_default=False)
        return super().save(*args, **kwargs)


class DemandRate(models.Model):
    """ demand rate """
    year = models.ForeignKey(Year, on_delete=PROTECT_CASCADE)
    age_group = models.ForeignKey(AgeGroup, on_delete=PROTECT_CASCADE)
    gender = models.ForeignKey(Gender, on_delete=PROTECT_CASCADE)
    demand_rate_set = models.ForeignKey(DemandRateSet, on_delete=PROTECT_CASCADE)
    value = models.FloatField(null=True)
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
