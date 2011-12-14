from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django_load.core import load_object

from ..models import Room, Message


class MessageHandler(object):
    """
    Class which implements two methods:
    - handle_received_message
        is designated to handle the "chat_message_received" signal
    - retrieve_messages
        is designated to return the list of messages sent into a chat room
            up to now

    'handle_received_message' method is designed to perform operations
        with the received message such that 'retrieve_messages' will be able to
        retrieve it afterwards

    The handlers can be customized extending this class
        and setting the full path name of the extending class
        into settings.CHATROOMS_HANDLERS_CLASS
    """

    def handle_received_message(self,
        sender, room_id, user, message, date, **kwargs):
        """
        Default handler for the message_received signal.
        1 - Saves an instance of message to db
        2 - Appends a tuple (message_id, message_obj)
            to the sender.messages queue
        3 - Signals the "New message" event on the sender
        4 - Returns the created message

        A handler is a method accepting the following arguments:
            signal, sender, room_id, user, message, date
        """
        # 1
        room = Room.objects.get(id=room_id)
        new_message = Message(user=user,
                              room=room,
                              date=date,
                              content=message)
        new_message.save()

        # 2
        msg_number = sender.get_next_message_id(room_id)
        messages_queue = sender.get_messages_queue(room_id)
        messages_queue.append((msg_number, new_message))

        # 3
        sender.signal_new_message_event(room_id)

        # 4
        return new_message

    def retrieve_messages(self,
        chatobj, room_id, *args, **kwargs):
        """
        Returns a list of tuples like:
        [(message_id, message_obj), ...]
        Where message_obj is an instance of Message or an object with
            the attributes 'username', 'date' and 'content' at least

        In this case, returns the queue of messages stored in
            the ChatView.message dictionary by self.handle_received_message
        """
        return chatobj.get_messages_queue(room_id)


class MessageHandlerFactory(object):
    """
    Returns a (singleton) instance of the class set as
        settings.CHATROOMS_HANDLERS_CLASS
        if any, else returns an instance of MessageHandler
    """
    _instance = None

    def __new__(cls):
        klass = MessageHandler
        if hasattr(settings, 'CHATROOMS_HANDLERS_CLASS'):
            try:
                klass = load_object(settings.CHATROOMS_HANDLERS_CLASS)
            except (ImportError, TypeError):
                raise ImproperlyConfigured(
                    "The class set as settings.CHATROOMS_HANDLERS_CLASS "
                    "does not exists"
                )

        if not cls._instance:
            cls._instance = klass()
        return cls._instance
