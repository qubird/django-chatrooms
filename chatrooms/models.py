#encoding=utf8

from django.db import models
from django.contrib.auth.models import User

from polymorphic import PolymorphicModel


class Room(PolymorphicModel):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField()
    subscribers = models.ManyToManyField(User, blank=True)
    private = models.NullBooleanField()
    password = models.CharField(max_length=32, blank=True)

    def __unicode__(self):
        return u"%s" % self.name

    @models.permalink
    def get_absolute_url(self):
        return ('room_view', [self.slug])


class Message(PolymorphicModel):
    user = models.ForeignKey(User)
    date = models.DateTimeField(['%Y-%m-%d %H:%M:%S:%f'])
    room = models.ForeignKey(Room)
    content = models.CharField(max_length=5000)
