from gevent import monkey
from gevent import __version__ as gevent_version
monkey.patch_all()

from django.core.management.commands import test


class Command(test.Command):
    def handle(self, *args, **kw):
        print "using GEvent %s" % gevent_version
        super(Command, self).handle(*args, **kw)
