from django.db import models
from ..infrastructure.models import Service
from ..population.models import RasterCell


class Mode(models.Model):
    '''
    modes available
    '''
    name = models.TextField()


class ModeVariant(models.Model):
    '''
    modes
    '''
    mode = models.ForeignKey(Mode, on_delete=models.RESTRICT)
    name = models.TextField()
    meta = models.JSONField()
    is_default = models.BooleanField()


class ReachabilityMatrix(models.Model):
    """Reachabliliy Matrix between raster cells with a mode variante"""
    from_cell = models.ForeignKey(RasterCell, on_delete=models.RESTRICT,
                                  related_name='from_cell')
    to_cell = models.ForeignKey(RasterCell, on_delete=models.RESTRICT,
                                related_name='to_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=models.RESTRICT)
    minutes = models.FloatField()


class Router(models.Model):
    """an OTP ROuter to use"""
    name = models.TextField()
    osm_file = models.TextField()
    tiff_file = models.TextField()
    gtfs_file = models.TextField()
    build_date = models.DateField()
    buffer = models.IntegerField()


class IndicatorTypes(models.TextChoices):
    """Indicator types"""
    TYPE1 = 'T1', 'Type1'
    TYPE2 = 'T2', 'Type2'


class Indicator(models.Model):
    """An Indicator"""
    indicator_type = models.CharField(max_length=2, choices=IndicatorTypes.choices)
    name = models.TextField()
    parameters = models.JSONField()
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)
