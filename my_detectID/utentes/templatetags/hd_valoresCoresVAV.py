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

    parametros = getLimiares()

    nome_param, (limiar1, limiar2, limiar3) = parametros[concept_id]
    # Dados
    df = trainKM()
    
    # Grupos
    df['grupo_' + nome_param] = df[nome_param].apply(
        lambda x:
        'Baixo' if x < limiar1 else
        'Normal Baixo' if x < limiar2 else
        'Normal Alto' if x < limiar3 else
        'Alto'
    )

    # Obter medicao do utente
    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=concept_id)
        .order_by('-measurement_datetime')
        .first()
    )


    if value < limiar1:
        grupo_ut = 'Baixo'
    elif value < limiar2:
        grupo_ut = 'Normal Baixo'
    elif value < limiar3:
        grupo_ut = 'Normal Alto'
    else:
        grupo_ut = 'Alto'

    # Tempo relativo do utente (em horas)
    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    grupos = df.groupby('grupo_' + nome_param)

    for grupo_nome, dados in grupos:
    
        if grupo_nome == grupo_ut:
            kmf = get_kaplan_model(concept_id,value,event_id)
            prob = kmf.predict(tempo_utente)

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