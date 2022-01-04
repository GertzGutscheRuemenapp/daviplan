from django.db import models
from django.contrib.gis.db import models as gis_models
from datentool_backend.base import NamedModel, JsonAttributes
from datentool_backend.infrastructure.models import (Service, Place,
                                                     Infrastructure)
from datentool_backend.population.models import RasterCell


class Mode(NamedModel, models.Model):
    '''
    modes available
    '''
    name = models.TextField()


class Stop(NamedModel, models.Model):
    """location of a public transport stop"""
    name = models.TextField()
    geom = gis_models.PointField(geography=True)


class ModeVariant(JsonAttributes, NamedModel, models.Model):
    '''
    modes
    '''
    mode = models.ForeignKey(Mode, on_delete=models.RESTRICT)
    name = models.TextField()
    meta = models.JSONField()
    is_default = models.BooleanField()
    cutoff_time = models.ManyToManyField(Infrastructure, through='CutOffTime')


class CutOffTime(models.Model):
    mode_variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)
    minutes = models.FloatField()


class MatrixCellPlace(models.Model):
    """Reachabliliy Matrix between raster cell and place with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=models.RESTRICT,
                             related_name='cell_place')
    place = models.ForeignKey(Place, on_delete=models.RESTRICT,
                              related_name='place_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=models.RESTRICT)
    minutes = models.FloatField()


class MatrixCellStop(models.Model):
    """Reachabliliy Matrix between raster cell and stop with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=models.RESTRICT,
                             related_name='cell_stop')
    stop = models.ForeignKey(Stop, on_delete=models.RESTRICT,
                             related_name='stop_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=models.RESTRICT)
    minutes = models.FloatField()


class MatrixPlaceStop(models.Model):
    """Reachabliliy Matrix between a place and stop with a mode variante"""
    place = models.ForeignKey(Place, on_delete=models.RESTRICT,
                             related_name='place_stop')
    stop = models.ForeignKey(Stop, on_delete=models.RESTRICT,
                             related_name='stop_place')
    variant = models.ForeignKey(ModeVariant, on_delete=models.RESTRICT)
    minutes = models.FloatField()


class MatrixStopStop(models.Model):
    """Reachabliliy Matrix between a stop and a stop with a mode variante"""
    from_stop = models.ForeignKey(Stop, on_delete=models.RESTRICT,
                                  related_name='from_stop')
    to_stop = models.ForeignKey(Stop, on_delete=models.RESTRICT,
                                related_name='to_stop')
    variant = models.ForeignKey(ModeVariant, on_delete=models.RESTRICT)
    minutes = models.FloatField()


class Router(NamedModel, models.Model):
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


class Indicator(JsonAttributes, NamedModel, models.Model):
    """An Indicator"""
    indicator_type = models.CharField(max_length=2, choices=IndicatorTypes.choices)
    name = models.TextField()
    parameters = models.JSONField()
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)
