#encoding=utf8

from django.template import RequestContext
from django.views.generic import ListView, DetailView

from .models import Room


class RoomsListView(ListView):
    """View to show the list of rooms available """
    context_object_name = "rooms"
    queryset = Room.objects.all()
    template_name = "chatrooms/rooms_list.html"
    paginate_by = 2


class RoomView(DetailView):
    """View for the single room """
    model = Room
    context_object_name = 'room'
    template_name = "chatrooms/room.html"
