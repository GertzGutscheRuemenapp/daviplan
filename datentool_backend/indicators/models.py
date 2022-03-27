from django.db import models
from django.contrib.gis.db import models as gis_models

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.utils.copy_postgres import DirectCopyManager

from datentool_backend.infrastructure.models import Place
from datentool_backend.modes.models import ModeVariant
from datentool_backend.population.models import RasterCell


class Stop(DatentoolModelMixin, NamedModel, models.Model):
    """location of a public transport stop"""
    name = models.TextField()
    geom = gis_models.PointField(srid=3857)

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixCellPlace(models.Model):
    """Reachabliliy Matrix between raster cell and place with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_place')
    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE,
                              related_name='place_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixCellStop(models.Model):
    """Reachabliliy Matrix between raster cell and stop with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixPlaceStop(models.Model):
    """Reachabliliy Matrix between a place and stop with a mode variante"""
    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE,
                              related_name='place_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_place')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixStopStop(models.Model):
    """Reachabliliy Matrix between a stop and a stop with a mode variante"""
    from_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                  related_name='from_stop')
    to_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                related_name='to_stop')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()

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