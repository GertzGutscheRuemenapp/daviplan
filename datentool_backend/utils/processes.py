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
    '''
    keeps track of running process in specific scopes and denies multiple
    processes to be run in parallel to avoid side effects

    Attributes
    ----------
    is_running : dict with scopes as keys and booleans as values
               status if any process is running in a specific scope
    user : dict with scopes as keys and Users as values
         user that currently runs a process in a specific scope
    '''
    is_running = {s: False for s in ProcessScope}
    user = {s: None for s in ProcessScope}
    def __init__(self, user: 'User', scope: ProcessScope = ProcessScope.GENERAL,
                 logger=None, blocked_by=[s for s in ProcessScope]):
        '''
        Parameters
        ----------
        user : User
             user trying to run the process
        scope : ProcessScope, optional
              scope of backend tasks (especially basedata uploads),
              defaults to GENERAL
        logger : Logger, optional
               logger to write errors to if blocked
               defaults to logger with lower name of scope
        blocked_by : list of scopes, optional
                   scopes that block this process from running if any of them
                   currently runs
                   defaults to all scopes
        '''
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
        #self.logger.info('Aufgabe erfolgreich abgeschlossen',
        self.logger.info('', extra={'status': {'success': True}})