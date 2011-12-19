#encoding=utf8

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (HttpResponse,
                         HttpResponseForbidden,
                         HttpResponseRedirect)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.decorators import available_attrs
from django.utils.functional import wraps

from ..models import Room


def ajax_user_passes_test_or_403(test_func, message="Access denied"):
    """
    Decorator for views that checks if the user passes the given test_func,
    raising 403 if it doesn't.
    If the request is ajax returns a 403 response with a message,
    else renders a 403.html template.
    The test should be a callable that takes a user object and
    returns True if the user passes.

    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request, request.user):
                return view_func(request, *args, **kwargs)
            # returns an HttpResponseForbidden if request is ajax
            if request.is_ajax:
                return HttpResponseForbidden(message)
            # else returns the 403 page
            ctx = RequestContext(request)
            resp = render_to_response('403.html', context_instance=ctx)
            resp.status_code = 403
            return resp
        return _wrapped_view
    return decorator


def ajax_room_login_required(view_func):
    """Handle non-authenticated users differently if it is an AJAX request
    If the ``allow_anonymous_access`` is set, allows access to anonymous

    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        room_id = request.REQUEST.get('room_id')
        if room_id:
            room = get_object_or_404(Room, pk=room_id)
            if room.allow_anonymous_access:
                return view_func(request, *args, **kwargs)
        if request.is_ajax():
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)
            else:
                response = HttpResponse()
                response['X-Django-Requires-Auth'] = True
                response['X-Django-Login-Url'] = settings.LOGIN_URL
                return response
        else:
            return login_required(view_func)(request, *args, **kwargs)
    return _wrapped_view


def room_check_access(view_func):
    """Decorator for RoomView detailed view.
    Deny access to unauthenticated users if room doesn't allow anon access
    Shows a form to set a guest user name if the room allows access
    to not authenticated users and the guest_name has not yet been set
    for the current session

    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        room_slug = kwargs.get('slug')
        room = get_object_or_404(Room, slug=room_slug)
        if request.user.is_authenticated():
            return view_func(request, *args, **kwargs)
        elif room.allow_anonymous_access:
            if not request.session.get('guest_name'):
                return HttpResponseRedirect(
                    # TODO: use django.http.QueryDict
                    reverse('set_guestname') + '?room_slug=%s' % room_slug)
            return view_func(request, *args, **kwargs)
        return login_required(view_func)(request, *args, **kwargs)
    return _wrapped_view


def signals_new_message_at_end(func):
    """Decorator for MessageHandler.handle_received_message method
    """
    @wraps(func, assigned=available_attrs(func))
    def _wrapper(self, sender, room_id, username, message, date, **kwargs):
        f = func(self, sender, room_id, username, message, date, **kwargs)
        sender.signal_new_message_event(room_id)
        return f
    return _wrapper


def waits_for_new_message_at_start(func):
    """Decorator for MessageHandler.retrieve_messages method
    """
    @wraps(func, assigned=available_attrs(func))
    def _wrapper(self, chatobj, room_id, *args, **kwargs):
        chatobj.wait_for_new_message(room_id)
        return func(self, chatobj, room_id, *args, **kwargs)
    return _wrapper
