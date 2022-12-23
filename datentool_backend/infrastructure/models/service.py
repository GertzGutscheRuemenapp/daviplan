from django.db import models

from datentool_backend.base import (NamedModel,
                                    DatentoolModelMixin,
                                    )

from datentool_backend.user.models import Profile
from .infrastructure import Infrastructure


DEFAULT_WORDING = {
    'capacity_singular_unit': 'Kapazitätseinheit',
    'capacity_plural_unit': 'Kapazitätseinheiten',
    'demand_singular_unit': 'Nachfragende:r',
    'demand_plural_unit': 'Nachfragende',
    'facility_singular_unit': 'Einrichtung',
    'facility_article': 'die',
    'facility_plural_unit':  'Einrichtungen',
}


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
                                       on_delete=models.CASCADE)
    editable_by = models.ManyToManyField(Profile,
                                         related_name='service_editable_by',
                                         blank=True)
    capacity_singular_unit = models.TextField(null=True, blank=True)
    capacity_plural_unit = models.TextField(null=True, blank=True)
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

    def save(self, **kwargs):
        super().save(**kwargs)
        for attribute, text in DEFAULT_WORDING.items():
            cur_text = getattr(self, attribute)
            if not cur_text:
                setattr(self, attribute, text)
        super().save()
