from django.db import models
from datentool_backend.base import NamedModel


class SiteSetting(NamedModel, models.Model):
    ''''''
    name = models.CharField(max_length=50, unique=True)
    title = models.TextField(default='Datentool')
    contact_mail = models.EmailField(default='', null=True, blank=True)
    logo = models.ImageField(null=True, blank=True)
    primary_color = models.CharField(default='#50AF32', max_length=30)
    secondary_color = models.CharField(default='#0390fc', max_length=30)
    welcome_text = models.TextField(default='Willkommen', null=True, blank=True)



