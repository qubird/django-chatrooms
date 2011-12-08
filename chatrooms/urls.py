from django.conf.urls.defaults import *

# URL patterns for django.chatrooms

urlpatterns = patterns('chatrooms',
	# Add url patterns here
	url(r'^get_messages/', 'ajax.chat.chat_get'),
)
