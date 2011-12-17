import json
import urlparse

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from chatrooms.models import Room
from chatrooms.utils.auth import get_login_url


class ChatroomsTest(TestCase):
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

    def test_anonymous_access(self):
        anon_room = Room(
                        allow_anonymous_access=True,
                        name="Anonymous Room",
                        slug="anonymous-room")
        login_req_room = Room(
                        allow_anonymous_access=False,
                        name="Login required room",
                        slug="login-required-room")
        anon_room.save()
        login_req_room.save()

        client = Client()

        response = client.get(login_req_room.get_absolute_url())
        # a login view may not have been implemented, so assertRedirects fails
        self.assertEquals(response.status_code, 302)
        import pdb; pdb.set_trace()
        url = response['Location']
        expected_url = get_login_url(login_req_room.get_absolute_url())
        e_scheme, e_netloc, e_path, e_query, e_fragment = urlparse.urlsplit(
                                                                expected_url)
        if not (e_scheme or e_netloc):
            expected_url = urlparse.urlunsplit(('http', 'testserver', e_path,
                e_query, e_fragment))
        self.assertEquals(url, expected_url)

        response = client.get(
            anon_room.get_absolute_url(),
            follow=True)

        # assert redirect
        self.assertRedirects(
            response,
            'http://testserver/chat/setguestname/?room_slug=anonymous-room')

        # post guestname
        guestname_posted = client.post(
            response.redirect_chain[0][0],
            {'guest_name': 'guest',
             'room_slug': 'anonymous-room'},
            follow=True)
        self.assertRedirects(
            guestname_posted,
            anon_room.get_absolute_url()
        )

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
