from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from datentool_backend.base import DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE


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
    is_default = models.BooleanField(default=False)
    is_prognosis = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.year}'