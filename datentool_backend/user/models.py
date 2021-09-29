from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.gis.db import models as gis_models
from datentool_backend.base import NamedModel


class Profile(models.Model):
    '''
    adds additional user information
    '''
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    admin_access = models.BooleanField(default=False)
    can_create_scenarios = models.BooleanField(default=False)
    can_edit_data = models.BooleanField(default=False)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    '''auto create profiles for new users'''
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    '''save profile when user is saved'''
    instance.profile.save()


class Project(NamedModel, models.Model):
    '''
    Basic Project Information
    '''
    name = models.TextField()
    owner = models.ForeignKey(Profile, on_delete=models.RESTRICT)
    users = models.ManyToManyField(Profile, related_name='shared_with_users')
    allow_shared_change = models.BooleanField()
    map_section = gis_models.PolygonField()

    @property
    def infrastructures(self):
        """set of infrastructures"""


class Scenario(NamedModel, models.Model):
    """BULE-Scenario"""
    name = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.RESTRICT)

    @property
    def demand(self):
        """set of demand rates"""

    @property
    def modes(self):
        """the modes used in the scenario"""
