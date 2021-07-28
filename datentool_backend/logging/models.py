from django.db import models
from django.contrib.gis.db import models as gis_models
from ..user.models import Profile
from ..infrastructure.models import Infrastructure, Service
from ..area.models import AreaLevel


class LogEntry(models.Model):
    """a generic log entry"""
    user = models.ForeignKey(Profile, on_delete=models.RESTRICT)
    date = models.DateField()
    text = models.TextField()

    class Meta:
        abstract = True


class CapacityUploadLog(LogEntry):
    """log entry for capacity uploads"""
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)


class PlaceUploadLog(LogEntry):
    """log entry for infrastructure uploads"""
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.RESTRICT)


class AreaUploadLog(LogEntry):
    """log entry for area uploads"""
    level = models.ForeignKey(AreaLevel, on_delete=models.RESTRICT)
