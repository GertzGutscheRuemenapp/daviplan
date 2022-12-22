import logging

from django_q.tasks import async_task
from django.conf import settings
from django.contrib.auth.models import User

from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response

from datentool_backend.site.models import ProcessScope, ProcessState

import channels.layers

channel_layer = channels.layers.get_channel_layer()


class RunProcessMixin:
    def run_sync_or_async(self,
                          func: callable,
                          user: User,
                          scope: ProcessScope,
                          message_async='Upload gestartet',
                          message_sync='Upload beendet',
                          ret_status=status.HTTP_202_ACCEPTED,
                          **params,
                          ):
        run_sync = not settings.USE_DJANGO_Q

        ppm = ProtectedProcessManager(
            user=user,
            scope=scope,
            run_sync=run_sync)

        if run_sync:
            try:
                ppm.run(func, **params)
            except Exception as e:
                msg = str(e)
                ppm.logger.error(msg)
                return Response({'Fehler': msg},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
            return Response({'message': message_sync},
                            status=ret_status)

        else:
            ppm.run(func, **params)
            return Response({'message': message_async},
                            status=status.HTTP_202_ACCEPTED)


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
    def __init__(self, user: 'User' = None,
                 scope: ProcessScope = ProcessScope.GENERAL,
                 logger=None,
                 blocked_by=[s for s in ProcessScope],
                 run_sync: bool = False):
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
        run_sync...

        '''
        self.me = user
        if not logger:
            logger = logging.getLogger(scope.name.lower())
        self.scope = scope
        self.logger = logger
        self.blocked_by = blocked_by
        self._async_running = False
        self._run_sync = run_sync

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

    def start_calculation(self):
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

    def finish(self, task):
        self.reset_state()
        status_msg = f'Berechnung im Bereich "{self.scope.label}"' \
            if self.scope else 'Berechnung'
        if task.success:
            self.logger.info(f'{status_msg} erfolgreich abgeschlossen.',
                             extra={'status': {'success': True,
                                               'finished': True}})
        else:
            self.logger.error(f'{status_msg} fehlgeschlagen.',
                              extra={'status': {'success': False,
                                                'finished': True}})

    def reset_state(self):
        state = self.get_state(self.scope, create=True)
        state.is_running = False
        state.save()

    def run(self, func, *args, **kwargs):
        self.start_calculation()
        if self._run_sync:
            try:
                func(*args, logger=self.logger, **kwargs)
            finally:
                self.reset_state()
        else:
            self.run_async(func, *args, logger=self.logger, **kwargs)

    def run_async(self, func, *args, **kwargs):
        self._async_func = func
        async_task(self._async_func_wrapper, *args, kwargs, hook=self.finish)

    def _async_func_wrapper(self, *args):
        self._async_func(*args[:-1], **args[-1])
