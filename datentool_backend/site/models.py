from django.db import models
from django.contrib.gis.db.models import MultiPolygonField
from datentool_backend.utils.models import SingletonModel
from datentool_backend.base import DatentoolModelMixin
from django.contrib.auth.models import User


class Year(DatentoolModelMixin, models.Model):
    """years available"""
    # site wide minimum year that can be set
    MIN_YEAR = 2011
    year = models.IntegerField(unique=True)
    is_default = models.BooleanField(default=False)
    # year is available to query prognosis data for
    is_prognosis = models.BooleanField(default=False)
    # year is available to query real data in for
    is_real = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.year}'


class ProjectSetting(SingletonModel):
    project_area = MultiPolygonField(null=True, srid=3857)


class SiteSetting(SingletonModel):
    name = models.CharField(max_length=50, unique=True)
    title = models.TextField(default='Datentool')
    contact_mail = models.EmailField(default='', null=True, blank=True)
    logo = models.ImageField(null=True, blank=True)
    primary_color = models.CharField(default='#50AF32', max_length=30)
    secondary_color = models.CharField(default='#0390fc', max_length=30)
    welcome_text = models.TextField(default='Willkommen', null=True, blank=True)
    bkg_user = models.TextField(default='', null=True, blank=True)
    regionalstatistik_user = models.TextField(default='', null=True, blank=True)
    # store passwords unhashed as plain text, because we need to retrieve and
    # send them in queries unhashed
    # ToDo: is this a security issue?
    bkg_password = models.TextField(default='', null=True, blank=True)
    regionalstatistik_password = models.TextField(
        default='', null=True, blank=True)


class ProcessScope(models.IntegerChoices):
    GENERAL = 1, 'Allgemein'
    POPULATION = 2, 'Bevölkerung'
    INFRASTRUCTURE = 3, 'Infrastruktur'
    ROUTING = 4, 'Routing'
    AREAS = 5, 'Gebiete'


class ProcessState(SingletonModel):
    scope = models.IntegerField(choices=ProcessScope.choices)
    is_running = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


