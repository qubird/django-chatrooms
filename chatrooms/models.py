from django.db import models
from django.contrib.auth.models import User


class Room(models.Model):
    subscribers = models.ManyToManyField(User)

    @models.permalink
    def get_absolute_url(self):
        return ('room_view', [str(self.id)])

    class Admin:
        pass


class Message(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(['%Y-%m-%d %H:%M:%S:%f'])
    microseconds = models.PositiveIntegerField()
    room = models.ForeignKey(Room)
    message = models.CharField(max_length=5000)

    class Admin:
        pass
