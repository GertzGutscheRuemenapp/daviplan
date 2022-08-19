from django.db import models

from datentool_backend.base import (NamedModel,
                                    DatentoolModelMixin,
                                    )
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE

from datentool_backend.area.models import (FieldType, MapSymbol)
from datentool_backend.user.models.profile import Profile


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
        except PlaceField.DoesNotExist:
            return ''


class InfrastructureAccess(models.Model):
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    allow_sensitive_data = models.BooleanField(default=False)


class PlaceField(DatentoolModelMixin, models.Model):
    """a field of a Place of this infrastructure"""
    name = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=PROTECT_CASCADE)
    field_type = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    is_label = models.BooleanField(null=True, default=None)
    sensitive = models.BooleanField(default=False)
    unit = models.TextField(blank=True, default='')

    class Meta:
        unique_together = [['infrastructure', 'name'],
                           ['infrastructure', 'is_label']]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.name} ({self.infrastructure.name})'


class Service(DatentoolModelMixin, NamedModel, models.Model):
    '''
    A Service provided by an infrastructure
    '''
    class WayRelationship(models.IntegerChoices):
        TO = 1
        FROM = 2
    class DemandType(models.IntegerChoices):
        QUOTA = 1
        FREQUENCY = 2
        UNIFORM = 3

    name = models.TextField()
    quota_type = models.TextField()
    description = models.TextField(blank=True)
    infrastructure = models.ForeignKey(Infrastructure,
                                       on_delete=PROTECT_CASCADE)
    editable_by = models.ManyToManyField(Profile,
                                         related_name='service_editable_by',
                                         blank=True)
    capacity_singular_unit = models.TextField(null=True, blank=True)
    capacity_plural_unit = models.TextField(null=True, blank=True)
    has_capacity = models.BooleanField(null=True, blank=True)
    demand_singular_unit = models.TextField(null=True, blank=True)
    demand_plural_unit = models.TextField(null=True, blank=True)
    demand_name = models.TextField(null=True, blank=True)
    demand_description = models.TextField(null=True, blank=True)
    has_capacity = models.BooleanField(default=True)
    facility_singular_unit = models.TextField(null=True, blank=True)
    facility_article = models.TextField(null=True, blank=True)
    facility_plural_unit = models.TextField(null=True, blank=True)
    direction_way_relationship = models.IntegerField(
        choices=WayRelationship.choices, default=WayRelationship.TO)
    demand_type = models.IntegerField(
        choices=DemandType.choices, default=DemandType.QUOTA)