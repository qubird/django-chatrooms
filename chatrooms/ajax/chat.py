# encoding: utf-8

import json
from datetime import datetime, timedelta
from collections import deque

from django.http import (HttpResponse, HttpResponseForbidden,
                        HttpResponseNotFound)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Max

from gevent.event import Event

from ..models import Room, Message
from ..utils.auth import check_user_is_subscribed
from ..utils.decorators import user_passes_test_or_403_with_ajax


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S:%f'


class Chat(object):
    def __init__(self):
        # define dictionary of chat room events,
        # keyed by roomId (for objects in ChatRoom)
        self.new_message_events = {}
        self.messages = {}
        self.connected_users = {}
        self.new_connected_user_event = {}
        rooms = Room.objects.all()
        for room in rooms:
            self.new_message_events[room.id] = Event()
            self.messages[room.id] = deque(maxlen=50)
            self.connected_users[room.id] = {}
            self.new_connected_user_event[room.id] = Event()
        # TODO: the signal_new_message_event could be not tight to a post_save
        #   signal, but to a generic "message_received" signal, which will be
        #   thrown by the message dispatcher function
        post_save.connect(self.signal_new_message_event, sender=Message)

    @method_decorator(login_required)
    @method_decorator(
        user_passes_test_or_403_with_ajax(check_user_is_subscribed))
    def chat_get(self, request):
        """handles ajax requests for messages
        TODO: a last_msg_id param may be sent to chat_get so that
            the method returns only the message with an id greater than
            the last_msg_id
        """
        try:
            room_id = request.GET['room_id']
        except KeyError:
            return HttpResponseNotFound('not found', mimetype="text/plain")
        room = Room.objects.get(id=room_id)
        # wait for new messages
        self.new_message_events[room.id].wait(20)
        messages = self.messages[room.id]
        to_jsonify = [
            {"message_id": message.pk,
             "username": message.user.username,
             "date": (message.date + timedelta(
                        microseconds=message.microseconds
                        )).strftime(TIME_FORMAT),
             "content": message.message}
             for message in messages
        ]
        return HttpResponse(json.dumps(to_jsonify),
                            mimetype="application/json")

    @method_decorator(login_required)
    @method_decorator(
        user_passes_test_or_403_with_ajax(check_user_is_subscribed))
    def chat_send(self, request):
        """handles messages sent by users
        """
        try:
            room_id = request.POST['room_id']
            message = request.POST['message']
            date = datetime.today()
        except KeyError:
            return HttpResponseNotFound('not found', mimetype="text/plain")
        user = request.user
        # TODO: call a dispatcher function instead of saving it directly to db:
        #   the dispatcher saves the message, or put it into a queue
        #   (ex. using a 0mq server, or whatever it does with the message),
        #   appends the message to queue and signals the room new_message_event
        room = Room.objects.get(id=room_id)
        microseconds = date.microsecond
        new_message = Message(user=user,
                          room=room,
                          date=date,
                          message=message,
                          microseconds=microseconds)
        new_message.save()
        return HttpResponse(date.strftime(TIME_FORMAT))

    def signal_new_message_event(self, sender, instance, *args, **kwargs):
        """appends created message to messages queue and
        notify new_message_event when a new message is saved into db
        """
        room = instance.room
        self.messages[room.id].append(instance)

        # signal event
        self.new_message_events[room.id].set()
        self.new_message_events[room.id].clear()

    @method_decorator(login_required)
    @method_decorator(
        user_passes_test_or_403_with_ajax(check_user_is_subscribed))
    def users_list_notify(self, request):
        """update user time into connected users dictionary"""
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

    @method_decorator(login_required)
    @method_decorator(user_passes_test_or_403_with_ajax(check_user_is_subscribed))
    def users_list_get(self, request):
        """dumps the list of connected users
        """
        REFRESH_TIME = 8
        try:
            room_id = request.GET['room_id']
        except KeyError:
            return HttpResponseNotFound('not found', mimetype="text/plain")
        # if request.user.is_authenticated():
        room_id = long(room_id)
        room = Room.objects.get(id=room_id)
        user = Utente.objects.get(username=request.user.username)
        self.connected_users[room.id].update({
                                user.username: datetime.today()
                            })
        self.new_connected_user_event[room_id].wait(REFRESH_TIME)
        # clean connected_users dictionary of disconnected users
        self.clean_connected_users(room_id)
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

    def clean_connected_users(self, room_id, seconds=60):
        """clean connected users dictionary of room_id of users not seen
            for seconds
        """
        now = datetime.today()
        for usr, date in self.connected_users[room_id].items():
            if (now - timedelta(seconds=seconds)) > date:
                self.connected_users[room_id].pop(usr)


chat = Chat()
chat_send = chat.chat_send
chat_get = chat.chat_get
users_list_get = chat.users_list_get
users_list_notify = chat.users_list_notify


def get_date(request):
    """dumps the current date """
    response = {
        "date": "%s" % datetime.today().strftime(TIME_FORMAT)
    }
    return HttpResponse(json.dumps(response),
                        mimetype="application/json")


def get_last_message_id(request):
    """dumps the greatest id found in Message table """
    max_id = Message.objects.aggregate(Max('id'))['id__max']
    val = max_id if max_id else -1
    response = {"id": val}
    return HttpResponse(json.dumps(response), mimetype="application/json")


@receiver(post_save, sender=Room)
def create_events_for_new_room(sender, **kwargs):
    """Creates an entry in Chat dictionary when a new room is created
    """
    if kwargs.get('created'):
        instance = kwargs.get('instance')
        room_id = instance.id
        chat.new_message_events[room_id] = Event()
        chat.messages[room_id] = deque(maxlen=50)
        chat.connected_users[room_id] = {}
        chat.new_connected_user_event[room_id] = Event()
