#encoding=utf8

from django.conf.urls.defaults import url, patterns

from . import views
from .utils.decorators import room_check_access


urlpatterns = patterns('chatrooms',
    # room views
    url(r'^rooms/$',
        views.RoomsListView.as_view(),
        name="rooms_list"),
    url(r'^room/(?P<slug>[-\w\d]+)/$',
        room_check_access(views.RoomView.as_view()),
        name="room_view"),
    url(r'^setguestname/$',
        views.GuestNameView.as_view(),
        name="set_guestname"),

    # ajax requests
    url(r'^get_messages/', 'ajax.chat.get_messages'),
    url(r'^send_message/', 'ajax.chat.send_message'),
    url(r'^get_latest_msg_id/', 'ajax.chat.get_latest_message_id'),
    url(r'^get_users_list/$', 'ajax.chat.get_users_list'),
    url(r'^notify_users_list/$', 'ajax.chat.notify_users_list')
)
