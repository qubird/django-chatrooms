from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import Signal

from django_load.core import load_object

from .models import Room, Message


chat_message_received = Signal(
    providing_args=[
        "room_id",
        "user",
        "message",
        "date",
])


def set_new_message_chatroom_event(chatobj, room_id):
    """
    Set event indexed by the given room_id on the ChatView object
    """
    event = chatobj.new_message_event[room_id]
    event.set()
    event.clear()


def db_message_received_handler(signal, sender, room_id, user, message, date):
    """
    Default handler for the message_received signal.
    1 - Saves an instance of message to db
    2 - Returns the created message

    A handler is a function accepting the following arguments:
        signal, sender, room_id, user, message, date
    It must return an object containing the following attributes:
        user, room, date, message
    Whatever the things you do with the message (store to db, queueing
        it to RabbitMQ or anything you like), you have to return
        an object with the former attributes.
    """
    room = Room.objects.get(id=room_id)
    new_message = Message(user=user,
                          room=room,
                          date=date,
                          message=message)
    new_message.save()
    return new_message


def get_message_received_handler():
    """
    Returns the function defined as settings.CHATROOMS_MESSAGE_RECEIVED_HANDLER
        if any, else returns the db_message_received_handler
    """
    if hasattr(settings, 'CHATROOMS_MESSAGE_RECEIVED_HANDLER'):
        try:
            return load_object(settings.CHATROOMS_MESSAGE_RECEIVED_HANDLER)
        except (ImportError, TypeError):
            raise ImproperlyConfigured(
            "The variable set as settings.CHATROOMS_MESSAGE_RECEIVED_HANDLER "
            "is not a module or the path is not correct"
            )
    return db_message_received_handler


chat_message_received.connect(get_message_received_handler())
