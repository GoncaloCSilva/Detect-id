from django import template
from django.http import HttpResponse
from ..models import Measurement, VisitOccurrence
from ..hd_utils import load_config, predict_survival, get_model


register = template.Library()

@register.simple_tag
def color_class_value(value, concept_id, person_id=None, event_id=1):
    """
    @brief Determines the color class based on a clinical value, concept, patient, and event.
    
    For categorical concepts 'prev' or 'Global', it returns a color based on the discrete value.
    Otherwise, it retrieves the latest measurement for the patient and concept, computes the survival
    probability using a model, and returns a color according to defined thresholds.

    @param value: Clinical value or state (int or float)
    @param concept_id: Clinical concept identifier (int or str)
    @param person_id: Patient ID (optional, int)
    @param event_id: Event ID (int, defaults to 1)

    @return: Corresponding color code (str) from configuration settings.
    """
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
            
    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=concept_id)
        .order_by('-measurement_datetime')
        .first()
    )

    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    model = get_model(concept_id,value,event_id)
    prob = predict_survival(model,tempo_utente)
    for i in range(0, num_states-1):
            if prob >= thresholds_states[i]:
                return color_states[i]
    
    return color_states[-1]  
    
@register.filter
def dict_value_first(value):
    """
    @brief Django template filter that returns the first value from a dictionary.
    
    Returns the first dictionary value if the input is a dict and not empty; otherwise returns an empty string.

    @param value: Dictionary object

    @return: The first value in the dictionary or empty string.
    """
    if isinstance(value, dict):
        return list(value.values())[0] if value else ''
    return ''

@register.filter
def get(dictionary, key):
    """
    @brief Django template filter to retrieve a value from a dictionary by key.
    
    @param dictionary: Dictionary object
    @param key: Key to look up in the dictionary

    @return: Value associated with the key or None if key is not present.
    """
    return dictionary.get(key)