from django import template
from django.http import HttpResponse
from lifelines import KaplanMeierFitter
import pandas as pd

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
def color_class_value(value, concept_id, person_id=None):

    if person_id == None:
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

        elif concept_id == 'FREQUÊNCIA CARDIACA':
            if 60 <= value <= 80:
                return 'greenBoxGood'
            elif 80 <= value < 100:
                return 'yellowBoxMedium'
            else:
                return 'redBoxBad'

        elif concept_id == 'TA Sistólica':
            if 0 <= value <= 129:
                return 'greenBoxGood'
            elif 130 <= value <= 140:
                return 'yellowBoxMedium'
            else:
                return 'redBoxBad'

        elif concept_id == 'TA Diastólica':
            if 0 <= value <= 80:
                return 'greenBoxGood'
            elif 81 <= value <= 90:
                return 'yellowBoxMedium'
            else:
                return 'redBoxBad'

        elif concept_id == 'TEMPERATURA':
            if 36 <= value <= 37.2:
                return 'greenBoxGood'
            elif 37.2 < value <= 38.0:
                return 'yellowBoxMedium'
            else:
                return 'redBoxBad'

        elif concept_id == 'NIVEL DE CONSCIÊNCIA':
            if 13 <= value <= 15:
                return 'greenBoxGood'
            elif 9 <= value < 12:
                return 'yellowBoxMedium'
            else:
                return 'redBoxBad'

        elif concept_id == 'DOR':
            if value == 1:
                return 'redBoxBad'
            else:
                return 'greenBoxGood'

                
            
        elif concept_id =='NECESSIDADE DE O2' :
            if value == 1:
                return 'redBoxBad'
            else:
                return 'greenBoxGood'

        return ''
    else:
    
        nome_param = concept_id
        parametros = {
        "SpO2": (1, [90, 95, 98]),
        "NECESSIDADE DE O2": (2, [1, 2, 3]),
        "FREQUÊNCIA CARDIACA": (3, [60, 100, 120]),
        "TA Sistólica": (4, [100.5, 119.5, 134.5]),
        "TA Diastólica": (5, [60, 80, 90]),
        "TEMPERATURA": (6, [35.5, 37.5, 38.5]),
        "NIVEL DE CONSCIÊNCIA": (7, [8, 13, 15]),
        "DOR": (8, [3, 6, 8]),
        }

        concept_id, (limiar1, limiar2, limiar3) = parametros[str(nome_param)]
        # Dados
        df = pd.read_csv("././detectid.csv", encoding='utf-8')
        df["Tempo"].fillna(df["Tempo"].median(), inplace=True)
        df[nome_param] = pd.to_numeric(df[nome_param], errors='coerce')
        df["DESCOMPENSAÇÃO"].fillna(0, inplace=True)
        
        
        # Grupos
        df['grupo_' + nome_param] = df[nome_param].apply(
            lambda x:
            'Baixo' if x < limiar1 else
            'Normal Baixo' if x < limiar2 else
            'Normal Alto' if x < limiar3 else
            'Alto'
        )

        print("DEBUG!!!!!!!!!!!!!!! -> ",person_id)
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
            kmf = KaplanMeierFitter()
            kmf.fit(dados['Tempo'], event_observed=dados["DESCOMPENSAÇÃO"], label=grupo_nome)
     
            if grupo_nome == grupo_ut:
                prob = kmf.predict(tempo_utente)

        if prob >= 0.6:
            return 'greenBoxGood'
        elif prob >= 0.4:
            return 'yellowBoxMedium'
        else:
            return 'redBoxBad'