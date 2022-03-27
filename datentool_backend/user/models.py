from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.area.models import MapSymbol, FieldType


class Profile(DatentoolModelMixin, models.Model):
    '''
    adds additional user information
    '''
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    admin_access = models.BooleanField(default=False)
    can_create_process = models.BooleanField(default=False)
    can_edit_basedata = models.BooleanField(default=False)
    settings = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    '''auto create profiles for new users'''
    if created:
        Profile(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    '''save profile when user is saved'''
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        pass


class Year(DatentoolModelMixin, models.Model):
    """years available"""
    year = models.IntegerField(unique=True)
    is_default = models.BooleanField(null=True)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.year}'


class PlanningProcess(DatentoolModelMixin, NamedModel, models.Model):
    '''
    Basic Project Information
    '''
    name = models.TextField()
    description = models.TextField(default='', blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.RESTRICT)
    users = models.ManyToManyField(Profile, related_name='shared_with_users',
                                   blank=True)
    allow_shared_change = models.BooleanField()


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
    unit = models.TextField()

    class Meta:
        unique_together = [['infrastructure', 'name'],
                           ['infrastructure', 'is_label']]


class Service(DatentoolModelMixin, NamedModel, models.Model):
    '''
    A Service provided by an infrastructure
    '''
    class WayRelationship(models.IntegerChoices):
        TO = 1
        FROM = 2

    name = models.TextField()
    quota_type = models.TextField()
    description = models.TextField(blank=True)
    infrastructure = models.ForeignKey(Infrastructure,
                                       on_delete=PROTECT_CASCADE)
    editable_by = models.ManyToManyField(Profile,
                                         related_name='service_editable_by',
                                         blank=True)
    capacity_singular_unit = models.TextField()
    capacity_plural_unit = models.TextField()
    has_capacity = models.BooleanField()
    demand_singular_unit = models.TextField()
    demand_plural_unit = models.TextField()
    demand_name = models.TextField(null=True, blank=True)
    demand_description = models.TextField(null=True, blank=True)
    has_capacity = models.BooleanField()
    facility_singular_unit = models.TextField(null=True, blank=True)
    facility_article = models.TextField(null=True, blank=True)
    facility_plural_unit = models.TextField(null=True, blank=True)
    direction_way_relationship = models.IntegerField(
        choices=WayRelationship.choices)