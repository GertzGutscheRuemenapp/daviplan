from django.db import models, transaction
from datentool_backend.base import (NamedModel,
                                    JsonAttributes,
                                    DatentoolModelMixin, )
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.infrastructure.models.infrastructures import Infrastructure


class Mode(models.IntegerChoices):
    WALK = 1, 'zu Fuß'
    BIKE = 2, 'Fahrrad'
    CAR = 3, 'Auto'
    TRANSIT = 4, 'ÖPNV'


class ModeVariant(DatentoolModelMixin, JsonAttributes, NamedModel, models.Model):
    '''
    modes
    '''
    mode = models.IntegerField(choices=Mode.choices)
    name = models.TextField()
    meta = models.JSONField(null=True)
    is_default = models.BooleanField(default=False)
    cutoff_time = models.ManyToManyField(Infrastructure, through='CutOffTime')

    def save(self, *args, **kwargs):
        # only one variant per mode can be a default
        if self.is_default:
            with transaction.atomic():
                ModeVariant.objects.filter(
                    is_default=True, mode=self.mode).update(is_default=False)
        return super().save(*args, **kwargs)


class CutOffTime(models.Model):
    mode_variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()
