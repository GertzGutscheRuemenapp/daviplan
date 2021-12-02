from django.db import models
from django.contrib.gis.db.models import GeometryField
from datentool_backend.models import AreaLevel


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class ProjectSetting(SingletonModel):
    project_area = GeometryField(null=True)
    start_year = models.IntegerField(default=2000)
    end_year = models.IntegerField(default=2020)


class BaseDataSetting(SingletonModel):
    default_pop_area_level = models.ForeignKey(AreaLevel, null=True,
                                               on_delete=models.SET_NULL)


class SiteSetting(models.Model):
    ''''''
    name = models.CharField(max_length=50, unique=True)
    title = models.TextField(default='Datentool')
    contact_mail = models.EmailField(default='', null=True, blank=True)
    logo = models.ImageField(null=True, blank=True)
    primary_color = models.CharField(default='#50AF32', max_length=30)
    secondary_color = models.CharField(default='#0390fc', max_length=30)
    welcome_text = models.TextField(default='Willkommen', null=True, blank=True)



