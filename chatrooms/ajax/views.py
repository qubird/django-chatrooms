# encoding: utf-8
import json

from django.http import (
                        HttpResponse,
                        HttpResponseForbidden,
                        HttpResponseNotFound)
from django.contrib.auth.decorators import login_required
from django.template import Context, Template

from livelessions.models import (
        Utente,
        CatalogoCorso,
        Room)


@login_required
def ajax_get_corsi(request):
    """
    Returns option fields of catalogo corso related to requested scheda corso and docente
    """
    id_scheda = request.REQUEST["schedacorso"]
    response = ''
    utente = Utente.objects.get(username=request.user.username)
    corsi = utente.corsi_as_docente.filter(fk_scheda_corso=id_scheda)
    response_template = Template("""
        {% for corso in corsi %}
        <option id="{{corso.pk_catalogo_corso}}">
            {{corso.edizione}}: {{corso.orario}}
        </option>
        {% endfor %}"""
    )
    ctx = Context({"corsi": corsi})
    response = response_template.render(ctx)
    return HttpResponse(response)


@login_required
def ajax_delete_room(request):
    """"""
    try:
        room_id = request.POST['room_id']
    except KeyError:
        return HttpResponseNotFound('not found', mimetype="text/plain")
    utente = Utente.objects.get(username=request.user.username)
    room = Room.objects.get(room_id=room_id)
    if room.publisher == utente:
        room.delete()
        return HttpResponse('ok', mimetype="text/plain")
    else:
        return HttpResponseForbidden('Forbidden access', mimetype="text/plain")


@login_required
def ajax_create_room(request):
    """"""
    try:
        id_corso = request.GET['id_corso']
    except KeyError:
        return HttpResponseNotFound('Not found', mimetype='text/plain')
    utente = Utente.objects.get(username=request.user.username)
    catalogo_corso = CatalogoCorso.objects.get(pk_catalogo_corso=id_corso)
    cat_corso_pk = catalogo_corso.pk
    try:
        catalogo_corso = utente.corsi_as_docente.get(
                                pk_catalogo_corso=id_corso)
    except DoesNotExist:
        return HttpResponseForbidden('Resource forbidden', 
                                    mimetype="text/plain")
    if utente.rooms_as_publisher_set.filter(corso=catalogo_corso).exists():
        error = {"error": "already_exists"}
        return HttpResponse(json.dumps(error),
                            mimetype='application/json')
    else:
        new_room = Room(corso=catalogo_corso, publisher=utente)
        new_room.save()
        response = {'room_id': new_room.id}
        return HttpResponse(json.dumps(response), mimetype='application/json')

