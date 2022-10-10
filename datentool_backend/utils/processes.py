from rest_framework.exceptions import PermissionDenied
from enum import Enum
from django_q.tasks import async_task
from datentool.loggers import send
from channels.generic.websocket import WebsocketConsumer
from aioredis import errors

import logging
import channels.layers

channel_layer = channels.layers.get_channel_layer()


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
    # for some undocumented reason django_q needs this attribute
    __name__ = 'ProtectedProcessManager'
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
        self._async_running = False
        a = ProcessConsumer()
        a.connect()

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
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if not self._async_running:
            self.finish()

    def finish(self):
        ProtectedProcessManager.is_running[self.scope] = False
        self._async_running = False
        self.logger.info('', extra={'status': {'success': True}})

    def emit_done(self, *args):
        send('cluster', 'done', log_type='cluster_message',
             status={'done': True, 'scope': self.scope.value})

    def run_async(self, func, *args, **kwargs):
        self._async_func = func
        self._async_running = True
        async_task(self._async_func_wrapper, *args, kwargs, hook=self.emit_done)

    def _async_func_wrapper(self, *args):
        self._async_func(*args[:-1], **args[-1])


class ProcessConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.channel_layer = channel_layer
        super().__init__(*args, **kwargs)

    def connect(self):
        '''join room'''
        self.room_name = 'cluster'
        print('hallo')
        try:
            self.channel_layer.group_add(
                    self.room_name,
                    'cluster123456'
                )
        except Exception as e:
            print(str(e))

    def disconnect(self, close_code):
        '''leave room'''
        self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    def cluster_message(self, event):
        '''send "log_message"'''
        print(f'cluster_message: {event} ')

    def receive(self, event):
        print(f'received: {event}')