from django.apps import AppConfig
from django.db.utils import DatabaseError


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datentool_backend'

    def ready(self):
        from datentool_backend.models import ProcessState
        # reset all process states on start
        try:
            ProcessState.objects.all().update(is_running=False)
        # thrown at migration, ProcessState does not exist yet
        except DatabaseError:
            pass

        from datentool_backend.utils.routers import OSRMRouter
        from datentool_backend.modes.models import Mode
        # run all routers on start
        for mode in [Mode.WALK, Mode.BIKE, Mode.CAR]:
            router = OSRMRouter(mode)
            if router.service_is_up and not router.is_running:
                router.run()
