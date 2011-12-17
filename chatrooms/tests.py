import json

from django.test import TestCase
from django.test.client import Client

from django.contrib.auth.models import User

from chatrooms.models import Room


class SimpleTest(TestCase):
    def create_user(self):
        # creates a user
        username = 'john'
        password = 'johnpasswd'
        email = 'john@beatles.com'
        user = User.objects.create_user(username=username,
                                        password=password,
                                        email=email)
        user.save()
        return username, password

    def test_get_messages(self, *args, **kwargs):
        username, password = self.create_user()

        # login user
        client = Client()
        client.login(username=username, password=password)

        # creates a room
        room = Room()
        room.save()

        # message queue empty: check last_message_id
        response = client.get('/chat/get_latest_msg_id/?room_id=%d' % room.id)
        json_response = json.loads(response.content)
        last_msg_id = json_response['id']
        self.assertEquals(last_msg_id, -1)

        # posts a message
        post_response = client.post('/chat/send_message/',
                                {'room_id': room.pk,
                                 'message': 'ABCD'},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(post_response.status_code, 200)
        json_response = json.loads(post_response.content)
        timestamp = json_response['timestamp']

        # gets list of messages
        response = client.get(
            '/chat/get_messages/?room_id=%d&latest_message_id=%d' % (
                                                room.id, last_msg_id),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        json_response = json.loads(response.content)

        expected_json = [{u'message_id': 0,
                          u'username': u'john',
                          u'date': timestamp,
                          u'content': u'ABCD', }]
        self.assertEquals(expected_json, json_response)

        # check last_message_id
        response = client.get('/chat/get_latest_msg_id/?room_id=%d' % room.id)
        json_response = json.loads(response.content)
        last_msg_id = json_response['id']
        self.assertEquals(last_msg_id, 0)
