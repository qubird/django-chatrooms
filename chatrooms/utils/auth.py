#encoding=utf8
from django.conf import settings
from django.core.exceptions import (ObjectDoesNotExist,
                                    ImproperlyConfigured,
)
from django_load.core import load_object


def get_test_user_function():
    """
    Returns the function set on settings.CHATROOMS_TEST_USER_FUNCTION
    if any, else returns False

    """
    if hasattr(settings, 'CHATROOMS_TEST_USER_FUNCTION'):
        try:
            return load_object(settings.CHATROOMS_TEST_USER_FUNCTION)
        except (ImportError, TypeError):
            raise ImproperlyConfigured(
                "The variable set as settings.CHATROOMS_TEST_USER_FUNCTION "
                "is not a module or the path is not correct"
            )
    return False

test_user_function = get_test_user_function()


def check_user_passes_test(request, user):
    """
    Returns the test_user_function if any,
    else returns True

    """
    if test_user_function:
        return test_user_function(request, user)
    return True
