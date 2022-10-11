import logging
import json
import time
import channels.layers
from aioredis import RedisError
from redis.exceptions import ConnectionError as RedisConnectionError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

import logging
logger = logging.getLogger(__name__)

channel_layer = channels.layers.get_channel_layer()

def send(channel: str, message: str, log_type: str='log_message',
         status={}, **kwargs):
    rec = {
        'message': message,
        'type': log_type,
        'timestamp': time.strftime('%d.%m.%Y %H:%M:%S'),
        'status': status,
    }
    rec.update(kwargs)
    async_to_sync(channel_layer.group_send)(channel, rec)


class WebSocketHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

    def emit(self, record):
        room = record.name
        status = getattr(record, 'status', {})
        try:
            send(room, record.getMessage(), log_type='log_message',
                 level=record.levelname, status=status)
        except (RedisError, RedisConnectionError, OSError) as e:
            logger.error(e)


class LogConsumer(WebsocketConsumer):
    def connect(self):
        '''join room'''
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        try:
            async_to_sync(self.channel_layer.group_add)(
                    self.room_name,
                    self.channel_name
                )

            self.accept()
        # redis is not up, what to do?
        except (RedisError, RedisConnectionError, OSError) as e:
            logger.error(e)

    def disconnect(self, close_code):
        '''leave room'''
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name,
            self.channel_name
        )

    def log_message(self, event):
        '''send "log_message"'''
        try:
            self.send(text_data=json.dumps({
                'message': event['message'],
                'level': event.get('level'),
                'timestamp': event.get('timestamp'),
                'status': event.get('status')
            }))
        except (RedisError, OSError, RedisConnectionError) as e:
            logger.error(e)