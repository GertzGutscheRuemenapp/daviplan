import logging
import datetime

from .models import LogEntry
from datentool_backend.user.models.profile import Profile


class PersistLogHandler(logging.StreamHandler):
    loggers = ['areas', 'population', 'infrastructure', 'routing']

    @classmethod
    def register(cls, user: Profile=None):
        handler = PersistLogHandler(user=user)
        for room in cls.loggers:
            logging.getLogger(room).addHandler(handler)

    def __init__(self, user: Profile=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.setLevel(logging.DEBUG)

    def emit(self, record):
        room = record.name
        entry = LogEntry.objects.create(
            date=datetime.datetime.now(), room=room, text=record.getMessage(),
            user=self.user, level=record.levelname)