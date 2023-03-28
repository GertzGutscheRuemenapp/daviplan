from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.db.models.functions import Lower

from datentool_backend.base import (NamedModel,
                                    DatentoolModelMixin,
                                    )
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE

from datentool_backend.area.models import (FieldType, MapSymbol)
from datentool_backend.user.models import Profile
from django.core.exceptions import ObjectDoesNotExist


class Infrastructure(DatentoolModelMixin, NamedModel, models.Model):
    '''
    Infrastructure that provide services
    '''

    name = models.TextField()
    description = models.TextField(blank=True)
    editable_by = models.ManyToManyField(
        Profile, related_name='infrastructure_editable_by', blank=True)
    accessible_by = models.ManyToManyField(
        Profile, related_name='infrastructure_accessible_by', blank=True,
        through='InfrastructureAccess')
    # sensitive_data
    order = models.IntegerField(unique=False, default=0)
    symbol = models.OneToOneField(MapSymbol, on_delete=models.SET_NULL,
                                  null=True, blank=True)

    @property
    def label_field(self) -> str:
        """the label field derived from the Fields"""
        try:
            return self.placefield_set.get(is_label=True).name
        except ObjectDoesNotExist:
            return ''

    def save(self, *args, **kwargs):
        """
        create table partitions for the Matrices
        referring to places of this infrastructure
        """

        super().save(*args, **kwargs)

        from datentool_backend.indicators.models import (ModeVariant,
                                                         MatrixPlaceStop,
                                                         MatrixCellPlace)
        for model in [MatrixCellPlace,
                      MatrixPlaceStop]:
            for variant in ModeVariant.objects.all():
                connection.schema_editor().add_list_partition(
                    model=model,
                    name=f"mode_{variant.pk}_infrastructure_{self.pk}",
                    values=[[variant.pk, self.pk]],
                )

    def delete(self, *args, **kwargs):
        """
        Delete the table partitions referencing this infrastructure
        before deleting the infrastructure
        """
        from datentool_backend.indicators.models import (ModeVariant,
                                                         MatrixPlaceStop,
                                                         MatrixCellPlace)
        for model in [MatrixCellPlace,
                      MatrixPlaceStop]:
            for variant in ModeVariant.objects.all():
                connection.schema_editor().delete_partition(
                    model=model,
                    name=f"mode_{variant.pk}_infrastructure_{self.pk}",
                )

        super().delete(*args, **kwargs)


class InfrastructureAccess(models.Model):
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    allow_sensitive_data = models.BooleanField(default=False)


class PlaceField(DatentoolModelMixin, models.Model):
    """a field of a Place of this infrastructure"""
    name = models.TextField()
    label = models.TextField(blank=True, default='')
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)
    field_type = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    is_label = models.BooleanField(null=True, default=None)
    sensitive = models.BooleanField(default=False)
    unit = models.TextField(blank=True, default='')
    is_preset = models.BooleanField(default=False)

    class Meta:
        constraints = [UniqueConstraint('infrastructure',
                                        Lower('name'),
                                        name='unique_infra_field_name_lower_constraint'),
                       UniqueConstraint('infrastructure',
                                        'is_label',
                                        name='unique_infra_field_is_label_constraint')]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.name} ({self.infrastructure.name})'
