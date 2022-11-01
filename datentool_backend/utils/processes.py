from rest_framework.exceptions import PermissionDenied
from datentool_backend.site.models import ProcessScope, ProcessState
from django_q.tasks import async_task

import logging
import channels.layers

channel_layer = channels.layers.get_channel_layer()


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
    # for some undocumented reason django_q needs this attribute
    __name__ = 'ProtectedProcessManager'
    def __init__(self, user: 'User' = None, scope: ProcessScope = ProcessScope.GENERAL,
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
        self._async_running = False

    @classmethod
    def is_running(cls, scope):
        state = cls.get_state(scope)
        if state:
            return state.is_running
        return False

    @classmethod
    def user(cls, scope):
        state = cls.get_state(scope)
        if state:
            return state.user
        return False

    @staticmethod
    def get_state(scope, create=False):
        try:
            state = ProcessState.objects.get(scope=scope.value)
            return state
        except ProcessState.DoesNotExist:
            if create:
                return ProcessState.objects.create(scope=scope.value)
        return

    def __enter__(self):
        blocking_scope = None
        for scope in self.blocked_by:
            if self.is_running(scope):
                blocking_scope = scope
                break
        if blocking_scope:
            user = self.user(blocking_scope)
            user_name = f'Nutzer:in "{user.username}"' if user \
                else 'Unbekannte:r Nutzer:in'
            msg = (f'{user_name} lädt momentan Daten im Bereich '
                   f'"{ProcessScope(blocking_scope).label}" hoch. Andere Uploads '
                   'sind währenddessen gesperrt. Bitte warten Sie bis '
                   'der Vorgang abgeschlossen ist und versuchen Sie es erneut.')
            self.logger.error(msg)
            raise PermissionDenied(msg)

        state = self.get_state(self.scope, create=True)
        state.is_running = True
        state.user = self.me
        state.save()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if not self._async_running:
            self.finish()

    def finish(self, *args):
        state = self.get_state(self.scope, create=True)
        state.is_running = False
        state.save()
        self._async_running = False
        self.logger.info('', extra={'status': {'success': True}})

    def run_async(self, func, *args, **kwargs):
        self._async_func = func
        self._async_running = True
        async_task(self._async_func_wrapper, *args, kwargs, hook=self.finish)

    def _async_func_wrapper(self, *args):
        self._async_func(*args[:-1], **args[-1])
