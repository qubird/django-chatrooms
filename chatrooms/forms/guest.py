from django import forms


class GuestNameForm(forms.Form):
    guest_name = forms.CharField(max_length=20)
    room_slug = forms.SlugField(widget=forms.HiddenInput())
