#encoding=utf8
import redis

from django.db.models import Max

from .handlers import MessageHandler
from ..models import Room, Message


class RedisMessageHandler(MessageHandler):
    """Custom MessageHandler class using redis
    for synchronization
    """
    def __init__(self):
        """Initializes redis connection
        """
        self.client = redis.Redis()
        self.pubsub = self.client.pubsub()

    def handle_received_message(self,
        sender, room_id, username, message, date, **kwargs):
        """
        1. saves the message
        2. publish a message to the redis client

        """

        room = Room.objects.get(id=room_id)
        fields = {
            'room': room,
            'date': date,
            'content': message,
            'username': username,
        }
        user = kwargs.get('user')
        if user:
            fields['user'] = user
        # 1
        new_message = Message(**fields)
        new_message.save()

        # 2
        self.client.publish('chatrooms', 'new message')

    def retrieve_messages(self, chatobj, room_id, latest_msg_id, **kwargs):
        """
        1. waits for "new message" on redis
        2. returns the list of latest messages

        """
        client = redis.Redis(socket_timeout=20)
        pubsub = client.pubsub()
        pubsub.subscribe('chatrooms')
        # 1
        msg = pubsub.listen().next()  # TODO: timeout?
        pubsub.unsubscribe('chatrooms')
        # 2
        messages = Message.objects.filter(room=room_id, id__gt=latest_msg_id)
        return [(msg.pk, msg) for msg in messages]

    def get_latest_message_id(self, chatobj, room_id):
        """Returns id of the latest message received """
        latest_msg_id = Message.objects.filter(
                        room=room_id).aggregate(
                        max_id=Max('id')).get('max_id')
        if not latest_msg_id:
            latest_msg_id = -1
        return latest_msg_id
