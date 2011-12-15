#encoding=utf8

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.decorators import available_attrs
from django.utils.functional import wraps


def ajax_user_passes_test_or_403(test_func, message="Access denied"):
    """
    Decorator for views that checks the user passes the given test,
    raising 403 if user does not pass test.
    If the request is ajax returns a 403 response with a message,
    else renders a 403.html template.
    The test should be a callable which takes the user object and
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
            ctx = RequestContext(request)
            resp = render_to_response('403.html', context_instance=ctx)
            resp.status_code = 403
            return resp
        return _wrapped_view
    return decorator


def ajax_login_required(view_func):
    """Handle non-authenticated users differently if it is an AJAX request
    Borrowed from django-hilbert
    """

    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
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


def signals_new_message_at_end(func):
    """Decorator for MessageHandler.handle_received_message method
    """

    @wraps(func, assigned=available_attrs(func))
    def _wrapper(self, sender, room_id, user, message, date, **kwargs):
        f = func(self, sender, room_id, user, message, date, **kwargs)
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
