from django import template
from django.http import HttpResponse
from lifelines import KaplanMeierFitter
import pandas as pd

from ..models import Measurement, VisitOccurrence

from ..hd_utils import load_config,getCurrentModel, getLimiares, predict_survival, trainModels, get_global_model, get_model


register = template.Library()

@register.simple_tag
def color_class_value(value, concept_id, person_id=None, event_id=1):
    try:
        event_id = int(event_id)
    except (TypeError, ValueError):
        event_id = event_id
    
    config = load_config()
    settings = config['general_settings']
    color_states = settings['color_states']
    num_states = settings['num_states']
    thresholds_states = settings['thresholds_states']

    if concept_id  == 'prev' or concept_id  == 'Global':
        for i in range(1, num_states + 1):
            if value == i:
                return color_states[i-1]
            
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

    model = get_model(concept_id,value,event_id)
    prob = predict_survival(model,tempo_utente)
    for i in range(0, num_states-1):
            if prob >= thresholds_states[i]:
                return color_states[i]
    
    return color_states[-1]  # Retorna a cor do último estado se nenhum outro for encontrado
    

@register.filter
def dict_value_first(value):
    if isinstance(value, dict):
        return list(value.values())[0] if value else ''
    return ''

@register.filter
def get(dictionary, key):
    """Filtro para obter o valor de um dicionário com a chave fornecida."""
    return dictionary.get(key)