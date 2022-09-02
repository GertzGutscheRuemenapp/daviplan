from django.db import models, transaction
import os

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
    Mode.CAR: 25,
}

MODE_MAX_DISTANCE = {
    Mode.WALK: 4000,
    Mode.BIKE: 10000,
    Mode.CAR: 25000,
    Mode.TRANSIT: 1000,
}

MODE_ROUTERS = {
    Mode.WALK: 'foot',
    Mode.BIKE: 'bicycle',
    Mode.CAR: 'car',
}

# default maximum walk time, insdead of transit use
DEFAULT_MAX_DIRECT_WALKTIME = 15


class Network(DatentoolModelMixin, NamedModel, models.Model):
    name = models.TextField(default='', blank=True)
    is_default = models.BooleanField(default=False)
    network_file = models.FileField(null=True)

    def save(self, *args, **kwargs):
        # only one network can be a default
        if self.is_default:
            Network.objects.filter(is_default=True).update(is_default=False)

        variants = []
        if self.pk is None:
            for mode in [Mode.WALK, Mode.BIKE, Mode.CAR]:
                variants.append(ModeVariant(network=self, mode=mode))
        super().save(*args, **kwargs)
        ModeVariant.objects.bulk_create(variants)


class ModeVariant(DatentoolModelMixin, models.Model):
    '''
    modes
    '''
    label = models.TextField(default='', blank=True)
    network = models.ForeignKey(Network, on_delete=models.CASCADE, null=True)
    mode = models.IntegerField(choices=Mode.choices)
    cutoff_time = models.ManyToManyField(Infrastructure, through='CutOffTime')
    is_default = models.BooleanField(default=False)

    def __repr__(self) -> str:
        return f'{Mode._value2label_map_[self.mode]} - {self.label}'

    def save(self, **kwargs):
        if self.pk is None and not self.network:
            try:
                self.network = Network.objects.get(is_default=True)
            except Network.DoesNotExist:
                pass
        if self.is_default:
            ModeVariant.objects.filter(
                is_default=True, network=self.network).update(is_default=False)
        super().save(**kwargs)


class CutOffTime(models.Model):
    mode_variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()
