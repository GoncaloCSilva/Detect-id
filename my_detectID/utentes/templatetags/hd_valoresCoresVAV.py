from django import template

register = template.Library()

@register.filter
def measurement_name(concept_id):
    mapping = {
        1: 'SpO2',
        2: 'O2',
        3: 'FC',
        4: 'TAS',
        5: 'TAD',
        6: 'Temp',
        7: 'GCS',
        8: 'Dor'
    }
    return mapping.get(concept_id, '')

@register.filter
def color_class(value, concept_id):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return ''

    if concept_id == 'SpO2':
        if value >= 95:
            return 'greenBoxGood'
        elif 90 <= value < 95:
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'

    elif concept_id == 'FC':
        if 60 <= value <= 80:
            return 'greenBoxGood'
        elif 80 <= value < 100:
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'

    elif concept_id == 'TAS':
        if 0 <= value <= 129:
            return 'greenBoxGood'
        elif 130 <= value <= 140:
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'

    elif concept_id == 'TAD':
        if 0 <= value <= 80:
            return 'greenBoxGood'
        elif 81 <= value <= 90:
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'

    elif concept_id == 'Temp':
        if 36 <= value <= 37.2:
            return 'greenBoxGood'
        elif 37.2 < value <= 38.0:
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'

    elif concept_id == 'GCS':
        if 13 <= value <= 15:
            return 'greenBoxGood'
        elif 9 <= value < 12:
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'

    elif concept_id == 'Dor':
        if value == 1:
            return 'redBoxBad'
        else:
            return 'greenBoxGood'

            
        
    elif concept_id =='O2' :
        if value == 1:
            return 'redBoxBad'
        else:
            return 'greenBoxGood'

    return ''
