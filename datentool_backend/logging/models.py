from django.db import models
from datentool_backend.base import NamedModel
from datentool_backend.user.models import Profile
from datentool_backend.infrastructure.models import Infrastructure, Service
from datentool_backend.area.models import AreaLevel
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE


class LogEntry(NamedModel, models.Model):
    """a generic log entry"""
    user = models.ForeignKey(Profile, on_delete=PROTECT_CASCADE)
    date = models.DateField()
    text = models.TextField()

    class Meta:
        abstract = True


class CapacityUploadLog(LogEntry):
    """log entry for capacity uploads"""
    service = models.ForeignKey(Service, on_delete=PROTECT_CASCADE)


class PlaceUploadLog(LogEntry):
    """log entry for infrastructure uploads"""
    infrastructure = models.ForeignKey(Infrastructure, on_delete=PROTECT_CASCADE)


class AreaUploadLog(LogEntry):
    """log entry for area uploads"""
    level = models.ForeignKey(AreaLevel, on_delete=PROTECT_CASCADE)
