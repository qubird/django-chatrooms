"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client

from django.contrib.auth.models import User

from chatrooms.models import Room


class SimpleTest(TestCase):
    def test_get_messages(self, *args, **kwargs):
    	# creates a user
    	username = 'john'
    	password = 'johnpasswd'
    	email = 'john@beatles.com'
    	user = User.objects.create_user(username=username,
    									password=password,
    									email=email)
    	user.save()

    	# login user
        client = Client()
        client.login(username=username, password=password)

    	# creates a room
    	room = Room()
    	room.save()

    	# check forbidden
        response = client.get('/chat/get_messages/?room_id=%d' % room.pk,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 403)
