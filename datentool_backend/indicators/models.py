from django.db import models
from django.contrib.gis.db import models as gis_models

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.utils.copy_postgres import DirectCopyManager

from datentool_backend.infrastructure.models.places import Place
from datentool_backend.modes.models import ModeVariant, Mode
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
    access_variant = models.ForeignKey(ModeVariant,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       related_name='mcp_access_variant')

    class Meta:
        unique_together = ['variant', 'access_variant', 'cell', 'place']
        constraints = [
            models.UniqueConstraint(
                name='variant_accessvariant_cell_place_uniq',
                fields=('variant', 'access_variant', 'cell', 'place')
            ),
            models.UniqueConstraint(
                name='variant_noaccessvariant_cell_place_uniq',
                fields=('variant', 'cell', 'place'),
                condition=models.Q(access_variant__isnull=True)
            )
        ]

    objects = models.Manager()
    copymanager = DirectCopyManager()


def get_default_access_variant():
    variant, created = ModeVariant.objects.get_or_create(mode=Mode.WALK, is_default=True)
    return variant.pk
    #return 1

def get_default_transit_variant():
    variant, created = ModeVariant.objects.get_or_create(mode=Mode.TRANSIT, is_default=True)
    return variant.pk
    #return 4



class MatrixCellStop(DatentoolModelMixin, models.Model):
    """Reachabliliy Matrix between raster cell and stop with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_cell')
    minutes = models.FloatField()
    access_variant = models.ForeignKey(ModeVariant,
                                       default=get_default_access_variant,
                                       on_delete=models.CASCADE,
                                       related_name='mcs_access_variant')

    class Meta:
        unique_together = ['access_variant', 'cell', 'stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixPlaceStop(models.Model):
    """Reachabliliy Matrix between a place and stop with a mode variante"""
    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE,
                              related_name='place_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_place')
    minutes = models.FloatField()
    access_variant = models.ForeignKey(ModeVariant,
                                       default=get_default_access_variant,
                                       on_delete=models.CASCADE,
                                       related_name='mps_access_variant')

    class Meta:
        unique_together = ['access_variant', 'place', 'stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()


class MatrixStopStop(models.Model):
    """Reachabliliy Matrix between a stop and a stop with a mode variante"""
    from_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                  related_name='from_stop')
    to_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                related_name='to_stop')
    minutes = models.FloatField()

    class Meta:
        unique_together = ['from_stop', 'to_stop']

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
