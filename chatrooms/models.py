#encoding=utf8

from django.db import models
from django.contrib.auth.models import User

from polymorphic import PolymorphicModel


class Room(PolymorphicModel):
    name = models.CharField(max_length=64)
    slug = models.SlugField()
    subscribers = models.ManyToManyField(User)
    private = models.BooleanField()
    password = models.CharField(max_length=32)

    @models.permalink
    def get_absolute_url(self):
        return ('room_view', [str(self.id)])


class Message(PolymorphicModel):
    user = models.ForeignKey(User)
    date = models.DateTimeField(['%Y-%m-%d %H:%M:%S:%f'])
    room = models.ForeignKey(Room)
    message = models.CharField(max_length=5000)
