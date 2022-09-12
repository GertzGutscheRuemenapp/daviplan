from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datentool_backend'

    def ready(self):
        from datentool_backend.logging.loggers import PersistLogHandler
        # handler to persist entries has to be added AFTER app is loaded
        # because it accesses models
        # ignoring user level by now (put it into login of user otherwise)
        PersistLogHandler.register()
