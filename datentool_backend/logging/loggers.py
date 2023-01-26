import logging
from django.utils import timezone
from django.conf import settings


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
            max_n_logs = getattr(settings, 'MAX_N_LOGS')
            if (max_n_logs):
                logs = LogEntry.objects.filter(room=room)
                diff = logs.count() - max_n_logs
                if (diff == 1):
                    logs.order_by('id').first().delete()
                elif (diff > 1):
                    ids = logs.order_by('id')[:diff].values_list('id')
                    LogEntry.objects.filter(id__in=ids).delete()
            LogEntry.objects.create(
                date=timezone.now(), room=room, text=message,
                user=self.user, level=record.levelname,
                status=getattr(record, 'status', None))
