from utils.handlers import MessageHandlerFactory
from django.dispatch import Signal


chat_message_received = Signal(
    providing_args=[
        "room_id",
        "username",
        "message",
        "date",
])

handler = MessageHandlerFactory()

chat_message_received.connect(handler.handle_received_message)
