====================
Django Chatrooms
====================

Chatrooms is an app that provides multi-user chat rooms for your django site.

It's completely based on jQuery and `gevent <http://www.gevent.org/>`_, whose libraries
have been used to implement long polling.

It provides a set of models, views and templates ready out of the box and easily
customizable.


Installation
************

Install the egg from pypi::

    $ pip install django-chatrooms

or get the latest revision from github::

    $ pip install -e git+git://github.com/qubird/django-chatrooms#egg=chatrooms

If you use buildout, just add ``django-chatrooms`` to your eggs part.

The egg setup takes care of installing all the needed dependencies, anyway you might need to install `greenlet <http://pypi.python.org/pypi/greenlet/>`_ and `libevent <http://www.libevent.org/>`_ to let gevent work properly.
 
Once the egg is installed, add the following apps to your settings.INSTALLED_APPS::

    INSTALLED_APPS = (
        # ...,
        'polymorphic',
        'chatrooms',
        # ...,
    )

Then include chatrooms urls to your urlpatterns::

    urlpatterns = patterns('',
        # ...,
        url(r'^chat/', include('chatrooms.urls')),
        # ...,
    )

Make sure you also added ``staticfiles_urlpatterns`` to urlconf like::

    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

and ``'django.contrib.staticfiles'`` is amongst ``INSTALLED_APPS``.

Then you're ready to run ``syncdb``.


Important Note
**************

django-chatrooms works properly in a multithreading environment (like `gevent patched wsgi server <https://github.com/gabrielfalcao/djangogevent>`_, or `uwsgi server with gevent plugin <http://projects.unbit.it/uwsgi/wiki/Gevent>`_).

The app does not work properly with servers that pre-fork the application before running, like  `gunicorn <http://gunicorn.org>`_ does.
That means you cannot run the application with *gunicorn* (setting ``--worker-class=gevent``) unless you use no more than 1 worker (setting ``--workers=1``).
To run the app in a multiprocess environment, you need some workaround implementing some sort of interprocess communication (ex. using a Message Queueing service like RabbitMQ).
See the `Message Handlers`_ section to know how.


Using the app
*************

Models
------
The app installs two models: Room and Message.
Rooms can be created by Admin Site.
Room objects have the following fields:

:name:
:description: almost self-explaining
:slug: which identifies the room in urls and views
:subscribers: which references a set of users (not used by default)
:allow_anonymous_access: which tells whether the room is accessible only to logged users, or event to "guests". A guest user is asked to choose a guest name before entering the room.
:private:
:password: These fields aren't used by default. They might be useful for implementing custom policies of access. See the `Custom access policies`_ section for further details.


Views
-----
Besides the core views that handle ajax requests to make the chat work, some class-based views have been designed.

These are in ``views.py``:

- ``RoomsListView``, which shows the list of rooms filtering the ones requiring a logged user if the user is not authenticated
- ``RoomView``, which renders the actual room page
- ``GuestNameView``, which is shown to non-logged users entering an ``allow_anonymous_access`` room to choose a guest name


Templates
---------
The templates you might want to override are

- ``chatrooms/guestname_form.html``, which is rendered by GuestNameView: it shows the form for choosing a guest name
- ``chatrooms/rooms_list.html``, which is rendered by RoomsListView
- ``chatrooms/room.html``, which is the skeleton of the page where chat objects are placed dynamically. The page includes the ``js/room.js`` script which requires a ``getContext()`` function like::

    <script type="text/javascript">
        getContext = function(){
            return {
                "username": "{{ user.username }}",
                "room_id": {{ room.id }},
            }
        }
    </script>


Some elements are required by ``room.js`` and need to be included in ``room.html``:

| ``#chatText``: an empty ``div``,
| ``#chatSendText``: text input where the user enters the text to send,
| ``#chatSendButton``: button input pressed by user to submit text,
| ``#connectedUsersList``: a list element where connected users are shown.


Styles
------
``static/css`` folder contains the file ``room.css`` you might want to override to re-style the room page.


Tests
-----
The ``test_gevent`` command has been implemented to test the chat features that use gevent libraries.


Message Handlers
****************

``utils.handlers.MessageHandler`` class implements the methods

- ``handle_received_message(sender, room_id, username, message, date, [user])``

    :sender: the ChatView instance
    :room_id: the id of the room where the message was sent
    :username: username or guest name of the user who sent the message
    :message: the content of the sent message
    :date: the timestamp of the sent message
    :user: request.user if user is authenticated, else ``None``

- ``retrieve_messages(chatobj, room_id)``

    :chatobj: the ChatView instance
    :room_id: the id of the room whose messages are requested

``handle_received_message`` method is designed to perform operations
with the received message such that ``retrieve_messages`` is able to
retrieve it afterwards.

``retrieve_messages`` must return a list of tuples like ``[(message_id, message_obj), ...]``, where ``message_obj`` is an instance of ``Message`` or an object with at least the following attributes:

- ``username``
- ``date``
- ``content``

and ``message_id`` is a unique progressive identifier.

To implement your handlers you need to create a class extending ``chatrooms.utils.handlers.MessageHandler``, say ``my.app.MyHandlerClass``,
override the aforementioned methods, and add to your settings::

    CHATROOMS_HANDLERS_CLASS = 'my.app.MyHandlerClass'

This way your defined methods will be used as default handlers for received messages and requests for messages.


See ``utils.handlers.MessageHandler`` and ``ajax.chat.ChatView`` docstrings for further details on these classes.


Custom access policies
**********************

Access to rooms can be controlled defining a function which takes ``request`` and ``user`` as arguments, and returns True or False whether the user is allowed to access the room or not (``room_id`` is given as a GET parameter of the request).

Once you defined your function, say ``my.app.user_can_enter_foo``, add to your settings::

    CHATROOMS_TEST_USER_FUNCTION = 'my.app.user_can_enter_foo'

Your function will be used as a test by view decorators.
When the user sends ajax requests to send or get chat messages, or get the connected users list, ``request`` and ``user`` are passed to your function.
If it returns ``False``, a 403 Forbidden Resource response is given, else the request is normally processed.


Acknowledgements
****************

`Denis Bilenko \'s webchat example <https://bitbucket.org/denis/gevent/src/tip/examples/webchat/>`_ has been a great starting point for the design of this app.
