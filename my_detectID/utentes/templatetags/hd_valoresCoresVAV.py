from django import template
from django.http import HttpResponse
from lifelines import KaplanMeierFitter
import pandas as pd

from utentes.hd_utils import getCurrentModel, getLimiares, predict_survival, trainModels, get_global_model, get_model
from utentes.models import Measurement, MeasurementExt, VisitOccurrence

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
        MeasurementExt.objects
        .filter(person_id=person_id, measurement_concept_id=concept_id)
        .order_by('-measurement_datetime')
        .first()
    )

    # Tempo relativo do utente (em horas)
    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600
    if getCurrentModel() == 1:
        if medicao.probability_km is None:
            model = get_model(concept_id,value,event_id)
            prob = predict_survival(model,tempo_utente)
            medicao.probability_km = prob
            medicao.save()
        else:
            prob = medicao.probability_km
    else:
        if medicao.probability_rsf is None:
            model = get_global_model(concept_id, value, event_id)
            prob = predict_survival(model, tempo_utente)
            medicao.probability_rsf = prob
            medicao.save()
        else:
            prob = medicao.probability_rsf

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