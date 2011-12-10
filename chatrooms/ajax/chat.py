# encoding: utf-8

import json
import itertools
from datetime import datetime, timedelta
from collections import deque

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import (HttpResponse,
                        HttpResponseNotFound,
                        HttpResponseBadRequest)
from django.utils.decorators import method_decorator

from gevent.event import Event

from ..models import Room, Message
from ..signals import chat_message_received
from ..utils.auth import check_user_passes_test
from ..utils.decorators import ajax_user_passes_test_or_403
from ..utils.decorators import ajax_login_required


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S:%f'

TIMEOUT = 20
if settings.DEBUG:
    TIMEOUT = 3


class ChatView(object):
    def __init__(self):
        # define dictionary of chat room events,
        # keyed by room_id (for objects in ChatRoom)
        self.new_message_events = {}
        self.messages = {}
        self.counters = {}
        self.connected_users = {}
        self.new_connected_user_event = {}
        rooms = Room.objects.all()
        for room in rooms:
            self.new_message_events[room.id] = Event()
            self.messages[room.id] = deque(maxlen=50)
            self.counters[room.id] = itertools.count()
            self.connected_users[room.id] = {}
            self.new_connected_user_event[room.id] = Event()

    @method_decorator(ajax_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def get_messages(self, request):
        """
        Handles ajax requests for messages
        Requests must contain room_id and latest_id
        """
        try:
            room_id = int(request.GET['room_id'])
            latest_id = int(request.GET['latest_id'])
        except:
            return HttpResponseNotFound('not found', mimetype="text/plain")
        room = Room.objects.get(id=room_id)
        # wait for new messages
        self.new_message_events[room.id].wait(TIMEOUT)
        messages = self.messages[room.id]
        to_jsonify = [
            {"message_id": msg_id,
             "username": message.user.username,
             "date": message.date.strftime(TIME_FORMAT),
             "content": message.message}
            for msg_id, message in messages
            if msg_id > latest_id
        ]
        return HttpResponse(json.dumps(to_jsonify),
                            mimetype="application/json")

    @method_decorator(ajax_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def send_message(self, request):
        """
        Gets room_id and message as request parameters and sends a
        chat_message_received signal
        """
        try:
            room_id = int(request.POST['room_id'])
            message = request.POST['message']
            date = datetime.now()
        except:
            return HttpResponseBadRequest()
        user = request.user

        foo, response = chat_message_received.send(
                            sender=self,
                            room_id=room_id,
                            user=user,
                            message=message,
                            date=date)[0]
        msg_number = self.counters[room_id].next()
        self.messages[room_id].append((msg_number, response))
        return HttpResponse(json.dumps(
                {'id': msg_number,
                 'timestamp': date.strftime(TIME_FORMAT), }
        ))

    @method_decorator(ajax_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def notify_users_list(self, request):
        """Updates user time into connected users dictionary
        """
        try:
            room_id = request.POST['room_id']
        except KeyError:
            return HttpResponseNotFound('not found', mimetype="text/plain")

        # if request.user.is_authenticated():
        room_id = long(room_id)
        user = request.user
        room = Room.objects.get(id=room_id)
        date = datetime.today()
        self.connected_users[room.id].update({user.username: date})
        self.new_connected_user_event[room_id].set()
        self.new_connected_user_event[room_id].clear()
        return HttpResponse('Connected')

    @method_decorator(ajax_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def get_users_list(self, request):
        """Dumps the list of connected users
        """
        REFRESH_TIME = 8
        try:
            room_id = request.GET['room_id']
        except KeyError:
            return HttpResponseBadRequest()
        room_id = int(room_id)
        room = Room.objects.get(id=room_id)
        user = User.objects.get(username=request.user.username)
        self.connected_users[room.id].update({
                                user.username: datetime.today()
                            })
        self.new_connected_user_event[room_id].wait(REFRESH_TIME)

        # clean connected_users dictionary of disconnected users
        self._clean_connected_users(room_id)
        json_users = [
            {"username": _user,
             "date": _date.strftime(TIME_FORMAT)}
            for _user, _date in self.connected_users[room_id].iteritems()
        ]
        json_response = {
            "now": datetime.today().strftime(TIME_FORMAT),
            "users": json_users,
            "refresh": str(REFRESH_TIME),
        }
        return HttpResponse(json.dumps(json_response),
                            mimetype='application/json')

    @method_decorator(ajax_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def get_last_message_id(self, request):
        """
        Dumps the id of the latest message sent
        """
        try:
            room_id = int(request.GET['room_id'])
        except:
            return HttpResponseBadRequest()
        latest_msg_id = -1
        msgs_queue = self.messages[room_id]
        if msgs_queue:
            latest_msg_id = msgs_queue[-1][0]
        response = {"id": latest_msg_id}
        return HttpResponse(json.dumps(response), mimetype="application/json")

    def _clean_connected_users(self, room_id, seconds=60):
        """clean connected users dictionary of room_id of users not seen
            for seconds
        """
        now = datetime.today()
        for usr, date in self.connected_users[room_id].items():
            if (now - timedelta(seconds=seconds)) > date:
                self.connected_users[room_id].pop(usr)


chat = ChatView()
send_message = chat.send_message
get_messages = chat.get_messages
get_users_list = chat.get_users_list
notify_users_list = chat.notify_users_list
get_last_message_id = chat.get_last_message_id


def get_date(request):
    """dumps the current date """
    response = {
        "date": "%s" % datetime.today().strftime(TIME_FORMAT)
    }
    return HttpResponse(json.dumps(response),
                        mimetype="application/json")


@receiver(post_save, sender=Room)
def create_events_for_new_room(sender, **kwargs):
    """Creates an entry in Chat dictionary when a new room is created
    """
    if kwargs.get('created'):
        instance = kwargs.get('instance')
        room_id = instance.id
        chat.new_message_events[room_id] = Event()
        chat.messages[room_id] = deque(maxlen=50)
        chat.counters[room_id] = itertools.count()
        chat.connected_users[room_id] = {}
        chat.new_connected_user_event[room_id] = Event()
