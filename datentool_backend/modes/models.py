from django.db import models
from datentool_backend.base import (NamedModel,
                                    JsonAttributes,
                                    DatentoolModelMixin, )
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.user.models import (Infrastructure)


class ModeChoice(models.IntegerChoices):
    WALK = 1, 'zu Fuß'
    BIKE = 2, 'Fahrrad'
    SQUARE = 3, 'Auto'
    TRANSIT = 4, 'ÖPNV'


class Mode(DatentoolModelMixin, NamedModel, models.Model):
    '''
    modes available
    '''
    name = models.TextField()


class ModeVariant(DatentoolModelMixin, JsonAttributes, NamedModel, models.Model):
    '''
    modes
    '''
    mode = models.ForeignKey(Mode, on_delete=PROTECT_CASCADE)
    #mode = models.IntegerField(choices=Mode.choices)
    name = models.TextField()
    meta = models.JSONField()
    is_default = models.BooleanField()
    cutoff_time = models.ManyToManyField(Infrastructure, through='CutOffTime')


class CutOffTime(models.Model):
    mode_variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()
