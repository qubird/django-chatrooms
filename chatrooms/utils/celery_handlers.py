#encoding=utf8

from celery.app import app_or_default
from celery.events import Event

from django.db.models import Max

from .handlers import MessageHandler
from ..models import Room, Message


class CeleryMessageHandler(MessageHandler):
    """Custom MessageHandler class using celery
    for synchronization
    """
    def __init__(self):
        """Initializes redis connections
        """
        self.app = app_or_default()
        self.event = Event(type='chatrooms')
        self.dispatcher = self.app.events.Dispatcher(
                            connection=self.app.broker_connection(),
                            enabled=True)

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

        self.dispatcher.send(type='chatrooms')

    def retrieve_messages(self, chatobj, room_id, latest_msg_id, **kwargs):
        """
        1. waits for a message on the queue
        2. returns the list of latest messages

        """
        def handler(*args, **kwargs):
            pass

        receiver = self.app.events.Receiver(
                    connection=self.app.broker_connection(),
                    handlers={"chatrooms": handler, })
        try:
            receiver.capture(limit=1, timeout=20, wakeup=True)
        except:
            pass

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
