#encoding=utf8

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, FormView

from .utils.auth import get_login_url
from .forms.guest import GuestNameForm
from .models import Room


class RoomsListView(ListView):
    """View to show the list of rooms available """
    context_object_name = "rooms"
    template_name = "chatrooms/rooms_list.html"
    paginate_by = 20

    def get_queryset(self):
        filters = {}
        if self.request.user.is_anonymous():
            filters['allow_anonymous_access'] = True
        return Room.objects.filter(**filters)


class RoomView(DetailView):
    """View for the single room """
    model = Room
    context_object_name = 'room'
    template_name = "chatrooms/room.html"


class GuestNameView(FormView):
    """Shows the form to choose a guest name to anonymous users """
    form_class = GuestNameForm
    template_name = 'chatrooms/guestname_form.html'

    def get_context_data(self, **kwargs):
        kwargs.update(super(GuestNameView, self).get_context_data(**kwargs))
        room_slug = self.request.GET.get('room_slug')
        next = ''
        if room_slug:
            next = reverse('room_view', kwargs={'slug': room_slug})
        kwargs['login_url'] = get_login_url(next)
        return kwargs

    def get_initial(self):
        init = super(GuestNameView, self).get_initial()
        room_slug = self.request.GET.get('room_slug')
        if room_slug:
            init.update(room_slug=room_slug)
        return init

    def form_valid(self, form):
        guest_name = form.cleaned_data.get('guest_name')
        room_slug = form.cleaned_data.get('room_slug')
        self.request.session['guest_name'] = guest_name
        if room_slug:
            redirect_url = reverse('room_view', kwargs={'slug': room_slug})
        else:
            redirect_url = reverse('rooms_list')
        return HttpResponseRedirect(redirect_url)
