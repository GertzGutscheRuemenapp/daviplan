from rest_framework.exceptions import PermissionDenied
from enum import Enum
import logging


class ProcessScope(Enum):
    GENERAL = 'Allgemein'
    POPULATION = 'Bevölkerung'
    INFRASTRUCTURE = 'Infrastruktur'
    ROUTING = 'Routing'
    AREAS = 'Gebiete'


class ProtectedProcessManager:
    is_running = {s: False for s in ProcessScope}
    user = {s: None for s in ProcessScope}
    def __init__(self, user, scope: ProcessScope = ProcessScope.GENERAL,
                 logger=None, blocked_by=[s for s in ProcessScope]):
        self.me = user
        if not logger:
            logger = logging.getLogger(scope.name.lower())
        self.scope = scope
        self.logger = logger
        self.blocked_by = blocked_by
    def __enter__(self):
        blocking_scope = None
        for scope in self.blocked_by:
            if self.is_running[scope]:
                blocking_scope = scope
                break
        if blocking_scope:
            user = self.user[blocking_scope]
            user_name = user.username if user else 'unbekannt'
            msg = (f'User "{user_name}" lädt momentan Daten im Bereich '
                   f'"{blocking_scope.value}" hoch. Andere Uploads '
                   'sind währenddessen gesperrt. Bitte warten Sie bis '
                   'der Vorgang abgeschlossen ist und versuchen Sie es erneut.')
            self.logger.error(msg)
            raise PermissionDenied(msg)
        ProtectedProcessManager.is_running[self.scope] = True
        ProtectedProcessManager.user[self.scope] = self.me
    def __exit__(self, exc_type, exc_value, exc_tb):
        ProtectedProcessManager.is_running[self.scope] = False