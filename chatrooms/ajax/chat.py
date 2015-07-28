# encoding: utf-8

import json
import itertools
from datetime import datetime, timedelta
from collections import deque

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from ..utils.compat import (HttpResponse,
                        HttpResponseBadRequest)
from django.utils.decorators import method_decorator

from gevent.event import Event

from ..models import Room
from ..signals import chat_message_received
from ..utils.auth import check_user_passes_test
from ..utils.decorators import ajax_user_passes_test_or_403
from ..utils.decorators import ajax_room_login_required
from ..utils.handlers import MessageHandlerFactory


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S:%f'

TIMEOUT = 30
if settings.DEBUG:
    TIMEOUT = 3


class ChatView(object):
    """Returns a singleton of ChatView
    Methods dispatch all the ajax requests from chat

    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            self = super(ChatView, cls).__new__(cls, *args, **kwargs)
            ChatView.__init__(self, *args, **kwargs)
            cls._instance = self
        return cls._instance

    def __init__(self):
        """
        Defines dictionary attibutes sorted by room_id
        For each room:
        - new_message_events contains gevent.Event objects used by message
          handlers to pause/restart execution and implement long polling
        - messages stores the queue of the latest 50 messages
        - counters contains iterators to pick up message identifiers
        - connected_users is a dictionary holding the usernames of connected
          users sorted by the time of their latest request
        - new_connected_user_event contains gevent.Event objects used
          by self.notify_users_list and self.get_users_list methods to
          implement long polling

        """
        self.handler = MessageHandlerFactory()
        self.new_message_events = {}
        self.messages = {}
        self.counters = {}
        self.connected_users = {}
        self.new_connected_user_event = {}
        rooms = Room.objects.all()
        for room in rooms:
            self.new_message_events[room.id] = Event()
            self.messages[room.id] = deque(maxlen=50)
            self.counters[room.id] = itertools.count(1)
            self.connected_users[room.id] = {}
            self.new_connected_user_event[room.id] = Event()

    def get_username(self, request):
        """Returns username if user is authenticated, guest name otherwise """
        if request.user.is_authenticated():
            username = request.user.username
        else:
            guestname = request.session.get('guest_name')
            username = '(guest) %s' % guestname
        return username

    def signal_new_message_event(self, room_id):
        """Signals new_message_event given a room_id """
        self.new_message_events[room_id].set()
        self.new_message_events[room_id].clear()

    def wait_for_new_message(self, room_id, timeout=TIMEOUT):
        """Waits for new_message_event given a room_id """
        self.new_message_events[room_id].wait(timeout)

    def get_messages_queue(self, room_id):
        """Returns the message queue given a room_id """
        return self.messages[room_id]

    def get_next_message_id(self, room_id):
        """Returns the next message identifier given a room_id """
        return self.counters[room_id].next()

    def get_connected_users(self, room_id):
        """Returns the connected users given a room_id"""
        return self.connected_users[room_id]

    @method_decorator(ajax_room_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def get_messages(self, request):
        """Handles ajax requests for messages
        Requests must contain room_id and latest_id
        Delegates MessageHandler.retrieve_message method to return the list
        of messages

        """
        try:
            room_id = int(request.GET['room_id'])
            latest_msg_id = int(request.GET['latest_message_id'])
        except:
            return HttpResponseBadRequest(
            "Parameters missing or bad parameters. "
            "Expected a GET request with 'room_id' and 'latest_message_id' "
            "parameters")

        messages = self.handler.retrieve_messages(
                        self, room_id, latest_msg_id)

        to_jsonify = [
            {"message_id": msg_id,
             "username": message.username,
             "date": message.date.strftime(TIME_FORMAT),
             "content": message.content}
            for msg_id, message in messages
            if msg_id > latest_msg_id
        ]
        return HttpResponse(json.dumps(to_jsonify),
                            mimetype="application/json")

    @method_decorator(ajax_room_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def send_message(self, request):
        """Gets room_id and message from request and sends a
        chat_message_received signal

        """
        try:
            room_id = int(request.POST['room_id'])
            message = request.POST['message']
            date = datetime.now()
        except:
            return HttpResponseBadRequest(
            "Parameters missing or bad parameters"
            "Expected a POST request with 'room_id' and 'message' parameters")
        user = request.user
        username = self.get_username(request)
        chat_message_received.send(
            sender=self,
            room_id=room_id,
            username=username,
            message=message,
            date=date,
            user=user if user.is_authenticated() else None)

        return HttpResponse(json.dumps({
                 'timestamp': date.strftime(TIME_FORMAT), }
        ))

    @method_decorator(ajax_room_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def notify_users_list(self, request):
        """Updates user time into connected users dictionary """
        try:
            room_id = int(request.POST['room_id'])
        except:
            return HttpResponseBadRequest(
            "Parameters missing or bad parameters"
            "Expected a POST request with 'room_id'")
        username = self.get_username(request)
        date = datetime.today()
        self.connected_users[room_id].update({username: date})
        self.new_connected_user_event[room_id].set()
        self.new_connected_user_event[room_id].clear()
        return HttpResponse('Connected')

    @method_decorator(ajax_room_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def get_users_list(self, request):
        """Dumps the list of connected users """
        REFRESH_TIME = 8
        try:
            room_id = int(request.GET['room_id'])
        except:
            return HttpResponseBadRequest(
            "Parameters missing or bad parameters"
            "Expected a POST request with 'room_id'")
        username = self.get_username(request)
        self.connected_users[room_id].update({
                                username: datetime.today()
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

    @method_decorator(ajax_room_login_required)
    @method_decorator(ajax_user_passes_test_or_403(check_user_passes_test))
    def get_latest_message_id(self, request):
        """Dumps the id of the latest message sent """
        try:
            room_id = int(request.GET['room_id'])
        except:
            return HttpResponseBadRequest()
        latest_msg_id = self.handler.get_latest_message_id(self, room_id)
        response = {"id": latest_msg_id}
        return HttpResponse(json.dumps(response), mimetype="application/json")

    def _clean_connected_users(self, room_id, seconds=60):
        """Remove from connected users dictionary users not seen
        for seconds

        """
        now = datetime.today()
        for usr, date in self.connected_users[room_id].items():
            if (now - timedelta(seconds=seconds)) > date:
                self.connected_users[room_id].pop(usr)


@receiver(post_save, sender=Room)
def create_events_for_new_room(sender, **kwargs):
    """Creates an entry in Chat dictionary attributes
    when a new room is created

    """
    if kwargs.get('created'):
        instance = kwargs.get('instance')
        room_id = instance.id
        chatview = ChatView()
        chatview.new_message_events[room_id] = Event()
        chatview.messages[room_id] = deque(maxlen=50)
        chatview.counters[room_id] = itertools.count(1)
        chatview.connected_users[room_id] = {}
        chatview.new_connected_user_event[room_id] = Event()
