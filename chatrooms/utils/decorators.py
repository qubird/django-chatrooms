#encoding=utf8

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.4 fallback.

from django.utils.decorators import available_attrs
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext


def user_passes_test_or_403_with_ajax(test_func, message="Access denied"):
    """
    Decorator for views that checks that the user passes the given test,
    raising 403 if user does not pass test.
    If the request is ajax returns a 403 response with a message,
    else renders a 403.html template.
    The test should be a callable that takes the user object and
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
