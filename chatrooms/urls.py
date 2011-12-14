#encoding=utf8

from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = patterns('chatrooms',
    # room views
    url(r'^rooms/$',
        login_required(views.RoomsListView.as_view()),
        name="rooms_list"),
    url(r'^room/(?P<slug>[-\w\d]+)/$',
        login_required(views.RoomView.as_view()),
        name="room_view"),

    # ajax requests
    url(r'^get_messages/', 'ajax.chat.get_messages'),
    url(r'^send_message/', 'ajax.chat.send_message'),
    url(r'^get_latest_msg_id/', 'ajax.chat.get_latest_message_id'),
    url(r'^get_users_list/$', 'ajax.chat.get_users_list'),
    url(r'^notify_users_list/$', 'ajax.chat.notify_users_list')
)
