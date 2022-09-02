from rest_framework.exceptions import PermissionDenied


class ProtectedProcessManager:
    is_running = False
    user = None
    def __init__(self, user, logger=None):
        self.me = user
        self.logger = logger
    def __enter__(self):
        if ProtectedProcessManager.is_running:
            user_name = ProtectedProcessManager.user.username \
                if ProtectedProcessManager.user else 'unbekannt'
            msg = (f'User "{user_name}" lädt momentan Daten hoch. Andere '
                   'Uploads sind währenddessen gesperrt. Bitte warten Sie bis '
                   'der Vorgang abgeschlossen ist und versuchen Sie es erneut.')
            if self.logger:
                self.logger.error(msg)
            raise PermissionDenied(msg)
        ProtectedProcessManager.is_running = True
        ProtectedProcessManager.user = self.me
    def __exit__(self, exc_type, exc_value, exc_tb):
        ProtectedProcessManager.is_running = False