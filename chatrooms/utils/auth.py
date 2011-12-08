#encoding=utf8

from django.core.exceptions import ObjectDoesNotExist


def check_user_is_subscribed(request, user):
    """returns True if the request user is subscribed to the request
        chat room, False otherwise
    """

    room_id = request.GET['room_id']
    try:
        user.room_set.get(pk=room_id)
        return True
    except ObjectDoesNotExist:
        return False
