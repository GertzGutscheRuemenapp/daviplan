from django.db import models
from datentool_backend.user.models import Profile


class LogEntry(models.Model):
    """a generic log entry"""
    user = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField()
    text = models.TextField()
    room = models.CharField(max_length=100)
    level = models.CharField(max_length=30)
    status = models.JSONField(null=True)

