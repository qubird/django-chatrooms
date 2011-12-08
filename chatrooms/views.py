# Create your views here.

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.contrib.auth.views import (
                            login as django_login,
                            logout as django_logout,
                            logout_then_login,
                            )

from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from livelessions.models import (
                            DocenteCorso,
                            Utente,
                            Room,
                            Iscritto)


def main_page(request):
    return render_to_response(
            'mainpage.html',
            {"title" : "main page",
    })


def login(request):
    """Check if user is authenticated and signed in FAD,
        shows user page or login form
    """
    if request.user and request.user.is_authenticated():
        # check is user is a Docente or a Studente and shows respecting page
        username = request.user.username
        # looks up Utente primary key to match
        try:
            pk_utente = Utente.objects.get(username=username).pk
        except Utente.DoesNotExist:
            # user not signed in FAD Backend
            return not_a_fad_user(request)
        if DocenteCorso.objects.filter(fk_utente=pk_utente).exists():
            # set is_a_doc flag to true for future authentication
            request.user.is_a_doc = True
            request.user.fad_id_utente = pk_utente
            return doc_page(request)
        elif Iscritto.objects.filter(fk_utente=pk_utente).exists():
            # check is utente is signed on any catalogo corso
            # set is_a_doc to false for future authentication
            request.user.is_a_doc = False
            return student_page(request)
        else:
            # utente is neither a studente nor a docente
            return not_any_course(request)
    else:
        #return django.contrib.auth.views.login function
        return django_login(request)


@login_required
def doc_page(request):
    """"""
    utente_id = request.user.fad_id_utente
    # retrieve utente object and rooms
    utente = Utente.objects.get(pk_utente=utente_id)
    rooms = utente.rooms_as_publisher_set.all()

    # retrieve corsi docente
    corsi = utente.corsi_as_docente.all()
    schede_corsi = []
    for c in corsi:
        if c.get_scheda_corso not in schede_corsi:
            schede_corsi.append(c.get_scheda_corso)
    context = {
        'username': request.user.username,
        'active_rooms': rooms,
        'schede_corsi': schede_corsi,
    }
    return render_to_response(
            "docpage.html",
            context,
            context_instance=RequestContext(request)
    )


@login_required
def student_page(request):
    utente = Utente.objects.get(username=request.user.username)
    corsi = utente.corsi_as_studente.all().values_list('pk', flat=True)
    rooms = Room.objects.filter(corso__in=corsi).order_by('corso')
    context = {
        "username": request.user.username,
        "active_rooms": rooms,
    }
    return render_to_response(
            "studentpage.html",
            context,
            context_instance=RequestContext(request)
    )


def not_a_fad_user(request):
    """
    Logs out an user existing in auth_user table but not signed on FAD backend
    """
    return django_logout(
        request,
        template_name='registration/not_a_fad_user.html'
    )


def not_any_course(request):
    return django_logout(
        request,
        template_name='registration/not_any_course.html'
    )


def logout(request):
    """
    if request.user and request.user.is_authenticated():
        django_logout(request)
        return login(request)
    else:
        return login(request)
    """
    return logout_then_login(request, '/')


@login_required
def room_view(request, room_id):
    """"""
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        return HttpResponseNotFound('Room not found!!')
    utente = Utente.objects.get(username=request.user.username)

    context = {
        'utente': request.user,
        'room': room
    }
    if utente.is_publisher(room_id):
        template = 'broadcaster.html'
    else:
        # user is either a subscriber or not authorised
        if utente.is_subscriber(room_id):
            template = 'subscriber.html'
        else:
            # utente iscritto al corso
            room = Room.objects.get(pk=room_id)
            corso = room.corso

            if utente.corsi_as_studente.filter(pk=corso.pk).exists():
                room.subscribers.add(utente)
                room.save()
                template = 'subscriber.html'
            else:
                return HttpResponseForbidden('Forbidden resource')
    return render_to_response(
        template,
        context,
        context_instance=RequestContext(request)
    )

