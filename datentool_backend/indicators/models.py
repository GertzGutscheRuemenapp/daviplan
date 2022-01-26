from typing import Dict

from django.db import models
from django.contrib.gis.db import models as gis_models
from datentool_backend.base import (NamedModel,
                                    JsonAttributes,
                                    DatentoolModelMixin,
                                    )
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE

from datentool_backend.user.models import Service
from datentool_backend.infrastructure.models import Place, FieldType
from datentool_backend.modes.models import ModeVariant
from datentool_backend.population.models import RasterCell


class Stop(DatentoolModelMixin, NamedModel, models.Model):
    """location of a public transport stop"""
    name = models.TextField()
    geom = gis_models.PointField(srid=3857)


class MatrixCellPlace(models.Model):
    """Reachabliliy Matrix between raster cell and place with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_place')
    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE,
                              related_name='place_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()


class MatrixCellStop(models.Model):
    """Reachabliliy Matrix between raster cell and stop with a mode variante"""
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE,
                             related_name='cell_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_cell')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()


class MatrixPlaceStop(models.Model):
    """Reachabliliy Matrix between a place and stop with a mode variante"""
    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE,
                             related_name='place_stop')
    stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                             related_name='stop_place')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()


class MatrixStopStop(models.Model):
    """Reachabliliy Matrix between a stop and a stop with a mode variante"""
    from_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                  related_name='from_stop')
    to_stop = models.ForeignKey(Stop, on_delete=PROTECT_CASCADE,
                                related_name='to_stop')
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)
    minutes = models.FloatField()


class Router(NamedModel, models.Model):
    """an OTP Router to use"""
    name = models.TextField()
    osm_file = models.TextField()
    tiff_file = models.TextField()
    gtfs_file = models.TextField()
    build_date = models.DateField()
    buffer = models.IntegerField()


class IndicatorType(NamedModel, models.Model):
    _indicator_classes: Dict[str, 'datentool_backend.indicators.compute.ComputeIndicator'] = {}

    name = models.TextField(unique=True)
    classname = models.TextField(unique=True)
    description = models.TextField()
    parameters = models.ManyToManyField(FieldType, through='IndicatorTypeFields')

    @classmethod
    def _update_indicators_types(cls):
        """check if all Indicators are in the database and add them, if not"""
        for classname, indicator_class in cls._indicator_classes.items():
            obj, created = IndicatorType.objects.get_or_create(classname=classname)
            obj.name = indicator_class.label
            obj.description = indicator_class.description
            obj.save()
            field_types = []
            for field_name, field_descr in indicator_class.parameters.items():
                field_type, created = FieldType.objects.get_or_create(
                    field_type=field_descr.value, name=field_name)
                field_types.append(field_type)
                itf, created = IndicatorTypeFields.objects.get_or_create(
                    indicator_type=obj, field_type=field_type)
                itf.label = field_name
                itf.save()
            deleted_fields = IndicatorTypeFields.objects.exclude(
                indicator_type=obj, field_type__in=field_types)
            deleted_fields.delete()
        deleted_types = IndicatorType.objects.exclude(classname__in=cls._indicator_classes.keys())
        deleted_types.delete()

    @classmethod
    def _add_indicator_class(cls, indicator_class):
        cls._indicator_classes[indicator_class.__name__] = indicator_class


class IndicatorTypeFields(models.Model):
    indicator_type = models.ForeignKey(IndicatorType, on_delete=PROTECT_CASCADE)
    field_type = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    label = models.TextField()


class Indicator(DatentoolModelMixin, JsonAttributes, NamedModel, models.Model):
    """An Indicator"""
    indicator_type = models.ForeignKey(IndicatorType, on_delete=PROTECT_CASCADE)
    name = models.TextField()
    parameters = models.JSONField()
    service = models.ForeignKey(Service, on_delete=PROTECT_CASCADE)
