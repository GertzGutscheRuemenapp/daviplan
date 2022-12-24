import logging
from django.utils import timezone


class PersistLogHandler(logging.StreamHandler):
    loggers = ['areas', 'population', 'infrastructure', 'routing']

    @classmethod
    def register(cls, user: 'Profile'=None) -> 'PersistLogHandler':
        handler = cls(user=user)
        for room in cls.loggers:
            logging.getLogger(room).addHandler(handler)
        return handler

    def __init__(self, user: 'Profile'=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.setLevel(logging.DEBUG)

    def emit(self, record):
        # import has to be done inside the function. when importing logger
        # in settings, app is not ready to import models
        from .models import LogEntry
        room = record.name
        message = record.getMessage()
        if message:
            LogEntry.objects.create(
                date=timezone.now(), room=room, text=message,
                user=self.user, level=record.levelname,
                status=getattr(record, 'status', None))
