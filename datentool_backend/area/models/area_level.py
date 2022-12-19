from django.db import models, transaction
from django.db.models import UniqueConstraint, Deferrable

from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.base import NamedModel, DatentoolModelMixin
from .layers import MapSymbol, Source


class AreaLevel(DatentoolModelMixin, NamedModel, models.Model):
    """an area level"""
    name = models.TextField()
    order = models.IntegerField(unique=False, default=0)
    symbol = models.OneToOneField(MapSymbol, on_delete=models.SET_NULL,
                                  null=True, blank=True)
    source = models.OneToOneField(Source, on_delete=models.SET_NULL, null=True,
                                  blank=True)
    is_active = models.BooleanField(default=True)
    is_preset = models.BooleanField(default=False)
    # level defaults to being the pop level for adding population entries
    is_default_pop_level = models.BooleanField(default=False)
    # level for pulling data from regionalstatistik
    is_statistic_level = models.BooleanField(default=False)
    # user set level for adding pop entries
    is_pop_level = models.BooleanField(default=False)
    max_population = models.FloatField(null=True)
    population_cache_dirty = models.BooleanField(default=True)

    @property
    def label_field(self) -> str:
        """the label field derived from the Fields"""
        try:
            return self.areafield_set.get(is_label=True).name
        except AreaField.DoesNotExist:
            return

    @label_field.setter
    def label_field(self, field_name: str):
        areafields = self.areafield_set.all()
        areafields.update(is_label=None)
        AreaField.objects.bulk_update(areafields, ['is_label'])
        try:
            label_field = self.areafield_set.get(name=field_name)
        except AreaField.DoesNotExist:
            raise ValueError(f'field {field_name} not found for {self}')
        label_field.is_label = True
        label_field.save()

    @property
    def key_field(self) -> str:
        """the label field derived from the Fields"""
        try:
            return self.areafield_set.get(is_key=True).name
        except AreaField.DoesNotExist:
            return

    @key_field.setter
    def key_field(self, field_name: str):
        areafields = self.areafield_set.all()
        areafields.update(is_key=None)
        AreaField.objects.bulk_update(areafields, ['is_key'])
        try:
            label_field = self.areafield_set.get(name=field_name)
        except AreaField.DoesNotExist:
            raise ValueError(f'field {field_name} not found for {self}')
        label_field.is_key = True
        label_field.save()

    def save(self, *args, **kwargs):
        # only one statistic / pop level at a time
        if self.is_statistic_level or self.is_pop_level:
            with transaction.atomic():
                if self.is_statistic_level:
                    AreaLevel.objects.filter(is_statistic_level=True)\
                        .update(is_statistic_level=False)
                if self.is_pop_level:
                    AreaLevel.objects.filter(is_pop_level=True)\
                        .update(is_pop_level=False)
        return super().save(*args, **kwargs)

    def delete(self, **kwargs):
        if self.symbol:
            self.symbol.delete()
        if self.source:
            self.source.delete()
        # deleting level marked as level to upload pop data with -> mark the
        # default one as the new pop level
        if self.is_pop_level:
            try:
                new_default = AreaLevel.objects.get(is_default_pop_level=True)
                new_default.is_pop_level = True
                new_default.save()
            except AreaLevel.DoesNotExist:
                pass
        return super().delete(**kwargs)


class FieldTypes(models.TextChoices):
    """enum for field types"""
    CLASSIFICATION = 'CLA', 'Classification'
    NUMBER = 'NUM', 'Number'
    STRING = 'STR', 'String'


class FieldType(DatentoolModelMixin, NamedModel, models.Model):
    """a generic field type"""
    ftype = models.CharField(max_length=3, choices=FieldTypes.choices)
    name = models.TextField()
    is_preset = models.BooleanField(default=False)

    def validate_datatype(self, data) -> bool:
        """validate the datatype of the given data"""
        if self.ftype == FieldTypes.NUMBER:
            return isinstance(data, (int, float))
        if self.ftype == FieldTypes.STRING:
            return isinstance(data, (str, bytes))
        if self.ftype == FieldTypes.CLASSIFICATION:
            return data in self.fclass_set.values_list('value', flat=True)


class FClass(DatentoolModelMixin, models.Model):
    """a class in a classification"""
    ftype = models.ForeignKey(FieldType, on_delete=models.CASCADE)
    order = models.IntegerField()
    value = models.TextField()

    class Meta:
        ordering = ['order']
        constraints = [UniqueConstraint(fields=['ftype', 'order'],
                                        name='fclass_unique',
                                        deferrable=Deferrable.DEFERRED)]

    def __str__(self) -> str:
        return (f'{self.__class__.__name__}: {self.ftype.name}: '
                f'{self.order} - {self.value}')


class AreaField(DatentoolModelMixin, models.Model):
    """a field of an Area"""
    name = models.TextField()
    area_level = models.ForeignKey(AreaLevel, on_delete=PROTECT_CASCADE)
    field_type = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    is_label = models.BooleanField(null=True, default=None)
    is_key = models.BooleanField(null=True, default=None)

    class Meta:
        unique_together = [['area_level', 'name'],
                           ['area_level', 'is_label'],
                           ['area_level', 'is_key'],
                           ]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.name} ({self.area_level.name})'
