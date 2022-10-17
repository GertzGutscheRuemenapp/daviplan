import logging
<<<<<<< HEAD
import datetime
from django.db.utils import InternalError
=======
from django.utils import timezone

>>>>>>> main

class PersistLogHandler(logging.StreamHandler):
    loggers = ['areas', 'population', 'infrastructure', 'routing']

    @classmethod
    def register(cls, user: 'Profile'=None):
        handler = PersistLogHandler(user=user)
        for room in cls.loggers:
            logging.getLogger(room).addHandler(handler)

    def __init__(self, user: 'Profile'=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.setLevel(logging.DEBUG)

    def emit(self, record):
        # import has to be done inside the function. when importing logger
        # in settings, app is not ready to import models
        from .models import LogEntry
        room = record.name
<<<<<<< HEAD
        try:
            entry = LogEntry.objects.create(
                date=datetime.datetime.now(), room=room, text=record.getMessage(),
                user=self.user, level=record.levelname)
        except InternalError:
            pass
=======
        message = record.getMessage()
        if message:
        	entry = LogEntry.objects.create(
            	date=timezone.now(), room=room, text=message,
            	user=self.user, level=record.levelname)
>>>>>>> main
