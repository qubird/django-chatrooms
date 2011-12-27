import json
import urlparse

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from chatrooms.ajax.chat import ChatView
from chatrooms.models import Room
from chatrooms.utils.auth import get_login_url


class ChatroomsTest(TestCase):
    def setUp(self):
        # creates a user
        self.username = 'john'
        self.userpwd = 'johnpasswd'
        self.useremail = 'john@beatles.com'
        self.user = User.objects.create_user(
                            username=self.username,
                            password=self.userpwd,
                            email=self.useremail)
        self.user.save()

    def test_chatview_attributes(self):
        """Asserts new items are added to ChatView instance
        when a new room is created, and these items are removed
        when a room is deleted

        """
        new_room = Room(name="New room",
                        slug="new-room")
        new_room.save()
        chatview = ChatView()
        self.assertIn(new_room.id, chatview.new_message_events)
        self.assertIn(new_room.id, chatview.messages)
        self.assertIn(new_room.id, chatview.connected_users)
        self.assertIn(new_room.id, chatview.counters)
        self.assertIn(new_room.id, chatview.new_connected_user_event)

        # works without a post_delete handler: somewhere the Django models
        #  collector gets rid of these items (awkward, not documented feat)
        new_room.delete()
        self.assertNotIn(new_room.id, chatview.new_message_events)
        self.assertNotIn(new_room.id, chatview.messages)
        self.assertNotIn(new_room.id, chatview.connected_users)
        self.assertNotIn(new_room.id, chatview.counters)
        self.assertNotIn(new_room.id, chatview.new_connected_user_event)

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
        username, password = self.username, self.userpwd

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

        expected_json = [{u'message_id': 1,
                          u'username': u'john',
                          u'date': timestamp,
                          u'content': u'ABCD', }]
        self.assertEquals(expected_json, json_response)

        # check last_message_id
        response = client.get('/chat/get_latest_msg_id/?room_id=%d' % room.id)
        json_response = json.loads(response.content)
        last_msg_id = json_response['id']
        self.assertEquals(last_msg_id, 1)
