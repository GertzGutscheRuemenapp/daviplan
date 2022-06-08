from django.core.exceptions import BadRequest


class ProtectedProcessManager:
    is_running = False
    user = None
    def __init__(self, user):
        self.me = user
    def __enter__(self):
        if ProtectedProcessManager.is_running:
            user_name = self.user.username if self.user else 'unbekannt'
            raise BadRequest(
                f'User "{user_name}" lädt momentan Daten hoch. Andere '
                'Uploads sind währenddessen gesperrt. Bitte warten Sie bis der '
                'Vorgang abgeschlossen ist und versuchen Sie es erneut.')
        ProtectedProcessManager.is_running = True
        self.user = self.me
    def __exit__(self, exc_type, exc_value, exc_tb):
        ProtectedProcessManager.is_running = False