from django.conf.urls.defaults import *

# URL patterns for django.chatrooms

urlpatterns = patterns('chatrooms',
    # Add url patterns here
    url(r'^get_messages/', 'ajax.chat.chat_get'),
    url(r'^send_message/', 'ajax.chat.chat_send'),
    url(r'^get_last_msg_id/', 'ajax.chat.get_last_message_id'),
)
