from django.db import models
from django.contrib.gis.db import models as gis_models

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.utils.copy_postgres import DirectCopyManager

from datentool_backend.infrastructure.models.places import Place
from datentool_backend.modes.models import ModeVariant
from datentool_backend.population.models import RasterCell


class Stop(DatentoolModelMixin, NamedModel, models.Model):
    """location of a public transport stop"""
    hstnr = models.IntegerField()
    name = models.TextField()
    geom = gis_models.PointField(srid=3857)
    variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)

    objects = models.Manager()
    copymanager = DirectCopyManager()

    class Meta:
        unique_together = [['variant', 'hstnr']]


class MatrixCellPlace(DatentoolModelMixin, models.Model):
    """Reachabliliy Matrix between raster cell and place with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_place')
    place = models.ForeignKey(Place, on_delete=models.CASCADE,
                              related_name='place_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)
    minutes = models.FloatField()
    access_variant = models.ForeignKey(ModeVariant, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ['variant', 'cell', 'place']

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixCellStop(DatentoolModelMixin, models.Model):
    """Reachabliliy Matrix between raster cell and stop with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)
    minutes = models.FloatField()
    access_variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['variant', 'cell', 'stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixPlaceStop(models.Model):
    """Reachabliliy Matrix between a place and stop with a mode variante"""
    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE,
                              related_name='place_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_place')
    variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)
    minutes = models.FloatField()
    access_variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['variant', 'place', 'stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixStopStop(models.Model):
    """Reachabliliy Matrix between a stop and a stop with a mode variante"""
    from_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                  related_name='from_stop')
    to_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                related_name='to_stop')
    variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)
    minutes = models.FloatField()

    class Meta:
        unique_together = ['variant', 'from_stop', 'to_stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()


class Router(NamedModel, models.Model):
    """an OTP Router to use"""
    name = models.TextField()
    osm_file = models.TextField()
    tiff_file = models.TextField()
    gtfs_file = models.TextField()
    build_date = models.DateField()
    buffer = models.IntegerField()
