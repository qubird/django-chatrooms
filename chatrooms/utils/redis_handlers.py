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
        """Initializes redis connections
        """
        self.client = redis.Redis()
        self.pubsub = self.client.pubsub()

    def handle_received_message(self,
        sender, room_id, username, message, date, **kwargs):
        """
        1. saves the message
        2. sends a message to the exchange

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
        msg_number = new_message.pk
        messages_queue = sender.get_messages_queue(room_id)
        messages_queue.append((msg_number, new_message))

        self.client.publish('chatrooms', 'new message')

    def retrieve_messages(self, chatobj, room_id, latest_msg_id, **kwargs):
        """
        1. waits for a message on the queue
        2. returns the list of latest messages

        """
        client = redis.Redis(socket_timeout=20)
        pubsub = client.pubsub()
        pubsub.subscribe('chatrooms')

        msg = pubsub.listen().next()  # TODO: timeout?
        pubsub.unsubscribe('chatrooms')
        messages = Message.objects.filter(room=room_id, id__gt=latest_msg_id)
        return [(msg.pk, msg) for msg in messages]

    def get_latest_message_id(self, chatobj, room_id):
        """Returns id of the latest retrieved message """
        latest_msg_id = Message.objects.filter(
                        room=room_id).aggregate(
                        max_id=Max('id')).get('max_id')
        if not latest_msg_id:
            latest_msg_id = -1
        return latest_msg_id
