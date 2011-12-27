from gevent import monkey
monkey.patch_all()

from django.core.management.commands import runserver


class Command(runserver.BaseRunserverCommand):
    def handle(self, *args, **options):
        """Apply gevent monkey patch and calls default runserver handler
        """
        super(Command, self).handle(*args, **options)
