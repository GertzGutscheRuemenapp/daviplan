import logging
import json
import channels.layers
from aioredis import errors
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

channel_layer = channels.layers.get_channel_layer()

def send(channel: str, message: str, log_type: str='log_message', **kwargs):
    rec = {
        'message': message,
        'type': log_type
    }
    rec.update(kwargs)
    async_to_sync(channel_layer.group_send)(channel, rec)


class WebSocketHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

    def emit(self, record):
        room = record.name
        try:
            send(room, self.format(record), log_type='log_message',
                 level=record.levelname)
        except errors.RedisError as e:
            print(e)


class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        '''join room'''
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        try:
            await self.channel_layer.group_add(
                    self.room_name,
                    self.channel_name
                )

            await self.accept()
        # redis is not up, what to do?
        except OSError as e:
            print(e)

    async def disconnect(self, close_code):
        '''leave room'''
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def log_message(self, event):
        '''send "log_message"'''
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'level': event.get('level'),
            'timestamp': event.get('timestamp')
        }))