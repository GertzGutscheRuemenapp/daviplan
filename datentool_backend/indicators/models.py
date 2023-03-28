from abc import abstractclassmethod

import pandas as pd

from django.db import models
from django.db.models import Count
from django.contrib.gis.db import models as gis_models

from psqlextra.types import PostgresPartitioningMethod
from psqlextra.models import PostgresPartitionedModel

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.utils.copy_postgres import DirectCopyManager

from datentool_backend.places.models import Place
from datentool_backend.modes.models import (ModeVariant,
                                            ModeVariantStatistic,
                                            get_default_access_variant,
                                            )

from datentool_backend.population.models import RasterCell


class Stop(DatentoolModelMixin, NamedModel, models.Model):
    """location of a public transport stop"""
    hstnr = models.IntegerField()
    name = models.TextField(blank=True)
    geom = gis_models.PointField(srid=3857)
    variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)

    objects = models.Manager()
    copymanager = DirectCopyManager()

    class Meta:
        unique_together = [['variant', 'hstnr']]


class MatrixMixin:
    _statistic: str = ''
    _variant_col = 'variant_id'
    _variant_relation = 'variant_id'

    @classmethod
    def get_n_rels(cls, variant: ModeVariant):
        """get the number of relations for the specified matrix"""
        variant_statistic, created = ModeVariantStatistic.objects\
            .get_or_create(variant=variant)
        cnt = getattr(variant_statistic, cls._statistic)
        # if statistic does not exist yet, calculate it from the matrix
        if cnt is None:
            cnt=cls._get_n_rels(variant)
            setattr(variant_statistic, cls._statistic, cnt)
            variant_statistic.save()
        return cnt

    @classmethod
    def set_n_rels(cls, variant: ModeVariant, value:int):
        variant_statistic = ModeVariantStatistic.objects.get(variant=variant)
        setattr(variant_statistic, cls._statistic, value)
        variant_statistic.save()

    @classmethod
    def add_n_rels(cls, df: pd.DataFrame):
        for variant_id, row in df.groupby(cls._variant_col).count().iterrows():
            new = row.iloc[0]
            cls.add_n_rels_for_variant(variant_id, new)

    @classmethod
    def add_n_rels_for_variant(cls, variant_id: int, new: int):
        variant = ModeVariant.objects.get(pk=variant_id)
        old = cls.get_n_rels(variant)
        total = old + new
        cls.set_n_rels(variant, total)

    @classmethod
    def remove_n_rels(cls, qs: 'MatrixMixin'):
        qs_cnt = qs.values(cls._variant_relation).annotate(cnt=Count('*'))
        for row in qs_cnt:
            variant = ModeVariant.objects.get(pk=row[cls._variant_relation])
            old = cls.get_n_rels(variant)
            total = old - row['cnt']
            cls.set_n_rels(variant, total)

    @abstractclassmethod
    def _get_n_rels(cls, variant: ModeVariant) -> int:
        raise NotImplementedError('To be defined in the subclass')


class MatrixCellPlace(MatrixMixin,
                      PostgresPartitionedModel,
                      DatentoolModelMixin):
    """Reachabliliy Matrix between raster cell and place with a mode variante"""
    _statistic: str = 'n_rels_place_cell'

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

    class PartitioningMeta:
        method = PostgresPartitioningMethod.LIST
        key = ["variant_id"]

    class Meta:
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

    @classmethod
    def _get_n_rels(cls, variant: ModeVariant) -> int:
        qs = cls.objects.filter(variant=variant)
        return qs.count()


class MatrixCellStop(MatrixMixin,
                      PostgresPartitionedModel,
                      DatentoolModelMixin):
    """Reachabliliy Matrix between raster cell and stop with a mode variante"""
    _statistic: str = 'n_rels_stop_cell'
    _variant_col = 'transit_variant_id'
    _variant_relation = 'stop__variant_id'

    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_cell')
    minutes = models.FloatField()
    access_variant = models.ForeignKey(ModeVariant,
                                       default=get_default_access_variant,
                                       on_delete=models.CASCADE,
                                       related_name='mcs_access_variant')
    transit_variant_id = models.IntegerField()


    class PartitioningMeta:
        method = PostgresPartitioningMethod.LIST
        key = ["transit_variant_id"]

    class Meta:
        unique_together = ['transit_variant_id', 'access_variant', 'cell', 'stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()

    @classmethod
    def _get_n_rels(cls, variant: ModeVariant) -> int:
        qs = cls.objects.filter(stop__variant=variant)
        return qs.count()

    def save(self, **kwargs):
        self.transit_variant_id = self.stop.variant_id
        return super().save(**kwargs)


class MatrixPlaceStop(MatrixMixin,
                      PostgresPartitionedModel):
    """Reachabliliy Matrix between a place and stop with a mode variante"""
    _statistic: str = 'n_rels_place_stop'
    _variant_col = 'transit_variant_id'
    _variant_relation = 'stop__variant_id'

    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE,
                              related_name='place_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_place')
    minutes = models.FloatField()
    access_variant = models.ForeignKey(ModeVariant,
                                       default=get_default_access_variant,
                                       on_delete=models.CASCADE,
                                       related_name='mps_access_variant')
    transit_variant_id = models.IntegerField()

    class PartitioningMeta:
        method = PostgresPartitioningMethod.LIST
        key = ["transit_variant_id"]

    class Meta:
        unique_together = ['transit_variant_id', 'access_variant', 'place', 'stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()

    @classmethod
    def _get_n_rels(cls, variant: ModeVariant) -> int:
        qs = cls.objects.filter(stop__variant=variant)
        return qs.count()

    def save(self, **kwargs):
        self.transit_variant_id = self.stop.variant_id
        return super().save(**kwargs)


class MatrixStopStop(MatrixMixin,
                     PostgresPartitionedModel):
    """Reachabliliy Matrix between a stop and a stop with a mode variante"""
    _statistic: str = 'n_rels_stop_stop'
    _variant_col = 'transit_variant_id'
    _variant_relation = 'from_stop__variant_id'

    from_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                  related_name='from_stop')
    to_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                related_name='to_stop')
    minutes = models.FloatField()
    variant_id = models.IntegerField()


    class PartitioningMeta:
        method = PostgresPartitioningMethod.LIST
        key = ["variant_id"]

    class Meta:
        unique_together = ['variant_id', 'from_stop', 'to_stop']

    objects = models.Manager()
    copymanager = DirectCopyManager()

    @classmethod
    def _get_n_rels(cls, variant: ModeVariant) -> int:
        qs = cls.objects.filter(from_stop__variant=variant)
        return qs.count()

    def save(self, **kwargs):
        self.variant_id = self.from_stop.variant_id
        return super().save(**kwargs)


class Router(NamedModel, models.Model):
    """an OTP Router to use"""
    name = models.TextField()
    osm_file = models.TextField()
    tiff_file = models.TextField()
    gtfs_file = models.TextField()
    build_date = models.DateField()
    buffer = models.IntegerField()
