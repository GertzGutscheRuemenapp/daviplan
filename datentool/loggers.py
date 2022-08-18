from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from aioredis import errors
import channels.layers

def send(channel: str, message: str, log_type: str='log_message', **kwargs):
    channel_layer = channels.layers.get_channel_layer()
    rec = {
        'message': message,
        'type': log_type
    }
    rec.update(kwargs)
    async_to_sync(channel_layer.group_send)(channel, rec)


class LogConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'log_{self.room_name}'
        # Join room group
        try:
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.accept()
        # redis is not up, what to do?
        except OSError as e:
            print(e)

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def log_message(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': event['message'],
            'level': event.get('level'),
            'timestamp': event.get('timestamp')
        }))