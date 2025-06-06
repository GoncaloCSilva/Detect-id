from django import template
from django.http import HttpResponse
from lifelines import KaplanMeierFitter
import pandas as pd

from utentes.hd_utils import getLimiares, trainKM, get_global_kaplan_model, get_kaplan_model
from utentes.models import Measurement, VisitOccurrence

register = template.Library()

@register.simple_tag
def color_class_value(value, concept_id, person_id=None, event_id=1):
    try:
        event_id = int(event_id)
    except (TypeError, ValueError):
        event_id = 1

    if concept_id  == 'prev' or concept_id  == 'Global':
        if value == 'Estável':
            return 'greenBoxGood'
        elif value == 'Moderado':
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'

    # Obter medicao do utente
    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=concept_id)
        .order_by('-measurement_datetime')
        .first()
    )

    # Tempo relativo do utente (em horas)
    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600


    km = get_kaplan_model(concept_id,value,event_id)
    prob = km.predict(tempo_utente)

    if prob >= 0.6:
        return 'greenBoxGood'
    elif prob >= 0.4:
        return 'yellowBoxMedium'
    else:
        return 'redBoxBad'
    

@register.filter
def dict_value_first(value):
    if isinstance(value, dict):
        return list(value.values())[0] if value else ''
    return ''