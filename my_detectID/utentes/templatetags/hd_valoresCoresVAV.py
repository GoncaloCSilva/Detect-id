from django import template
from django.http import HttpResponse
from lifelines import KaplanMeierFitter
import pandas as pd

from utentes.hd_utils import get_csv_data, get_kaplan_model
from utentes.models import Measurement, VisitOccurrence

register = template.Library()

@register.filter
def measurement_name(concept_id):
    mapping = {
        1: 'SpO2',
        2: 'NECESSIDADE DE O2',
        3: 'FREQUÊNCIA CARDIACA',
        4: 'TA Sistólica',
        5: 'TA Diastólica',
        6: 'TEMPERATURA',
        7: 'NIVEL DE CONSCIÊNCIA',
        8: 'DOR'
    }
    return mapping.get(concept_id, '')

@register.simple_tag
def color_class_value(value, concept_id, person_id=None, event_id=1):
    try:
        event_id = int(event_id)
    except (TypeError, ValueError):
        event_id = 1

    if concept_id == 'prev':
        if value == 'Estável':
            return 'greenBoxGood'
        elif value == 'Moderado':
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'



    nome_param = concept_id
    parametros = {
    "SpO2": (1, [90, 95, 98]),
    "NECESSIDADE DE O2": (2, [1, 2, 3]),
    "FREQUÊNCIA CARDIACA": (3, [60, 100, 120]),
    "TA Sistólica": (4, [100.5, 119.5, 134.5]),
    "TA Diastólica": (5, [60, 80, 90]),
    "TEMPERATURA": (6, [35.5, 37.5, 38.5]),
    "NIVEL DE CONSCIÊNCIA": (7, [8, 13, 15]),
    "DOR": (8, [1,2,3]),
    }

    eventos = {
        1:"DESCOMPENSAÇÃO",
        2:"Ativação Médico",
        3:"Aumento da Vigilância",
        4:"Via Área Ameaçada"
    }

    evento = eventos[event_id]

    concept_id, (limiar1, limiar2, limiar3) = parametros[str(nome_param)]
    # Dados
    df = get_csv_data()
    
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
            kmf = get_kaplan_model(concept_id,value)
            prob = kmf.predict(tempo_utente)

    if prob >= 0.6:
        return 'greenBoxGood'
    elif prob >= 0.4:
        return 'yellowBoxMedium'
    else:
        return 'redBoxBad'