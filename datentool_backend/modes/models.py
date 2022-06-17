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

MODE_SPEED = {
    Mode.WALK: 3.5,
    Mode.BIKE: 10.5,
    Mode.CAR: 25
}

MODE_MAX_DISTANCE = {
    Mode.WALK: 4000,
    Mode.BIKE: 10000,
    Mode.CAR: 25000
}


class Network(DatentoolModelMixin, NamedModel, models.Model):
    name = models.TextField()
    is_default = models.BooleanField(default=False)
    network_file = models.FileField(null=True)

    def save(self, *args, **kwargs):
        # only one network can be a default
        if self.is_default:
            Network.objects.filter(is_default=True).update(is_default=False)
        return super().save(*args, **kwargs)


class ModeVariant(DatentoolModelMixin, models.Model):
    '''
    modes
    '''
    network = models.ForeignKey(Network, on_delete=models.CASCADE, null=True)
    mode = models.IntegerField(choices=Mode.choices)
    cutoff_time = models.ManyToManyField(Infrastructure, through='CutOffTime')


class CutOffTime(models.Model):
    mode_variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()
