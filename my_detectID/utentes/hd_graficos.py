import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import KaplanMeierFitter
from io import BytesIO
import matplotlib.pyplot as plt
from django.http import HttpResponse
import pandas as pd

from utentes.hd_utils import get_global_model, getLimiares, trainModels, get_model
from .models import Measurement, PersonExt, VisitOccurrence

    # TABELA DE LIMIARES PARA CADA PARAMETRO #
    # Nivel de Consciencia 	- < 13.5	- Baixo
    # 			    	    - 13.5 - 14.5	- Intermédio
    # 			            - >= 14.5	- Normal

    # Frequencia Cardiaca	- < 69.5	- Baixo
    # 			            - 69.5 - 84.5	- Normal Baixo
    # 			            - 84.5 - 100.5	- Normal Alto
    # 			            - >= 100.5	- Alto

    # TA Sistólica	    	- < 100.5	- Baixo
    # 			            - 100.5 - 119.5	- Normal Baixo
    # 			            - 119.5 - 134.5	- Normal Alto
    # 			            - >= 134.5	- Alto

    # TA Diastólica		    - < 55.5	- Baixo
    # 		        	    - 55.5 - 65.5	- Normal Baixo
    # 		        	    - 65.5 - 76.5	- Normal Alto
    # 		        	    - >= 76.5	- Alto

    # Temperatura		    - < 36.05	- Baixo
    # 		        	    - 36.05 - 36.55	- Normal Baixo
    # 		        	    - 36.55 - 37.05	- Normal
    # 		        	    - >= 37.05	- Alto

    # SpO2			        - < 90.5	- Muito Baixo
    # 		        	    - 90.5 - 93.5	- Baixo
    # 		        	    - 93.5 - 95.5	- Normal Baixo
    # 		        	    - >= 95.5	- Normal
    
def graphicPatient_km(person_id, param_id, evento_id, tempoPrev = None):
    """
    @brief Gera gráfico de sobrevivência para qualquer parâmetro clínico com destaque para o utente.
    @param person_id ID do utente.
    @param param_id ID do parâmetro (1 a 8).
    @param evento_id ID do evento (1 a 4).
    @return HttpResponse com imagem PNG.
    """
    param_id = int(param_id)
    try:
        evento_id = int(evento_id)
    except:
        evento_id = 1  
        
    parametros = getLimiares()

    eventos = {
        1: "Descompensação",
        2: "Ativação Médico",
        3: "Aumento da Vigilância",
        4: "Via Área Ameaçada",
        5: "Suporte Ventilatório",
        6: "Suporte Circulatório",
        7:  "Mortalidade"
    }

    if param_id not in parametros:
        return HttpResponse("Parâmetro inválido", status=400)
    if evento_id not in eventos:
        return HttpResponse("Evento inválido", status=400)
    
    nome_param, (limiar1, limiar2) = parametros[param_id]
    evento_nome = eventos[evento_id]
    

    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=param_id)
        .order_by('-measurement_datetime')
        .first()
    )

    if not medicao:
        return HttpResponse(f"Medição de {nome_param} não encontrada para este utente", status=404)

    valor = medicao.value_as_number

    if valor < limiar1:
        grupo_ut = 'Baixo'
        valor2 = limiar1
        grupo_2 = 'Normal'
        valor3 = limiar2
        grupo_3 = 'Alto'

    elif valor < limiar2:
        grupo_ut = 'Normal'
        valor2 = 0
        grupo_2 = 'Baixo'
        valor3 = limiar2
        grupo_3 = 'Alto'
        
    else:
        grupo_ut = 'Alto'
        valor2 = 0
        grupo_2 = 'Baixo'
        valor3 = limiar1
        grupo_3 = 'Normal'



    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhspan(0.6, 1, color='green', alpha=0.2)
    ax.axhspan(0.4, 0.6, color='yellow', alpha=0.2)
    ax.axhspan(0, 0.4, color='red', alpha=0.2)

    
    cores = {
        'Baixo': 'blue',
        'Normal': 'green',
        'Alto': 'red'
    }

    kmf = get_model(param_id,valor,evento_id)
    kmf.plot_survival_function(ax=ax, ci_show=False, color=cores.get(grupo_ut, 'black'))
    
    if param_id!=2 and param_id !=8 and param_id != 6:
        kmf2 = get_model(param_id,valor2,evento_id)
        kmf2.plot_survival_function(ax=ax, ci_show=False, color=cores.get(grupo_2, 'black'))
    if param_id!= 8:
        kmf3 = get_model(param_id,valor3,evento_id)
        kmf3.plot_survival_function(ax=ax, ci_show=False, color=cores.get(grupo_3, 'black'))

    prob = kmf.predict(tempo_utente)
    ax.scatter(tempo_utente, prob, color=cores[grupo_ut], s=100, zorder=3, label=f"Utente")   
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')
    
    if tempoPrev is not None:
        tempoPrev = int(tempoPrev)
        prob = kmf.predict(tempo_utente+tempoPrev)
        ax.scatter(tempo_utente+tempoPrev, prob, color='yellow', s=100, zorder=3, label=f"Previsão")   
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    plt.title(f"Estatistico - {nome_param} ({grupo_ut}) - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de não ocorrer {evento_nome}")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')

def graphicPatient_rsf(person_id, param_id, evento_id,tempoPrev = None):
    """
    @brief Gera gráfico de sobrevivência RSF para qualquer parâmetro clínico com destaque para o utente.
    @param person_id ID do utente.
    @param param_id ID do parâmetro (1 a 8).
    @param evento_id ID do evento (1 a 7).
    @return HttpResponse com imagem PNG.
    """
    import numpy as np
    from matplotlib import pyplot as plt
    from io import BytesIO
    from lifelines.utils import datetimes_to_durations

    param_id = int(param_id)
    evento_id = int(evento_id)
    
    parametros = getLimiares()
    eventos = {
        1: "Descompensação",
        2: "Ativação Médico",
        3: "Aumento da Vigilância",
        4: "Via Área Ameaçada",
        5: "Suporte Ventilatório",
        6: "Suporte Circulatório",
        7: "Mortalidade"
    }

    if param_id not in parametros or evento_id not in eventos:
        return HttpResponse("Parâmetro ou evento inválido", status=400)

    nome_param, (limiar1, limiar2) = parametros[param_id]
    evento_nome = eventos[evento_id]

    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=param_id)
        .order_by('-measurement_datetime')
        .first()
    )
    if not medicao:
        return HttpResponse(f"Medição de {nome_param} não encontrada para este utente", status=404)

    valor = medicao.value_as_number

    if valor < limiar1:
        grupo_ut = 'Baixo'
        valor2 = limiar1
        grupo_2 = 'Normal'
        valor3 = limiar2
        grupo_3 = 'Alto'

    elif valor < limiar2:
        grupo_ut = 'Normal'
        valor2 = 0
        grupo_2 = 'Baixo'
        valor3 = limiar2
        grupo_3 = 'Alto'
        
    else:
        grupo_ut = 'Alto'
        valor2 = 0
        grupo_2 = 'Baixo'
        valor3 = limiar1
        grupo_3 = 'Normal'

    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    rsf = get_model(param_id, evento_id)
    if rsf is None:
        return HttpResponse("Modelo RSF não encontrado", status=404)


  
    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhspan(0.6, 1, color='green', alpha=0.2)
    ax.axhspan(0.4, 0.6, color='yellow', alpha=0.2)
    ax.axhspan(0, 0.4, color='red', alpha=0.2)

    cores = {
        'Baixo': 'blue',
        'Normal': 'green',
        'Alto': 'red'
    }

    ax.step(rsf[0].x, rsf[0].y, where="post", color=cores.get(grupo_ut, 'black'), label=grupo_ut)

    if param_id!=2 and param_id !=8:
        rsf2 = get_model(param_id,valor2,evento_id)
        ax.step(rsf2[0].x, rsf2[0].y, where="post", color=cores.get(grupo_2, 'black'), label=grupo_2)
    if param_id!= 8:
        rsf3 = get_model(param_id,valor3,evento_id)
        ax.step(rsf3[0].x, rsf3[0].y, where="post", color=cores.get(grupo_3, 'black'), label=grupo_3)

    try:
        prob = np.interp(tempo_utente, rsf[0].x, rsf[0].y)
    except:
        prob = 0.0

    ax.scatter(tempo_utente, prob, color=cores[grupo_ut], s=100, zorder=3, label=f"Utente")
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    if tempoPrev is not None:
        tempoPrev = int(tempoPrev)
        try:
            prob = np.interp(tempo_utente+tempoPrev, rsf[0].x, rsf[0].y)
        except:
            prob = 0.0
        
        ax.scatter(tempo_utente+tempoPrev, prob, color='yellow', s=100, zorder=3, label=f"Previsão")
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')


    plt.title(f"Aprendizagem Automática - {nome_param} ({grupo_ut}) - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de não ocorrer {evento_nome}")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')



def graphicPatientGlobal(person_id,tempoPrev=None):
    kmf = get_global_model()

    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    medicao = Measurement.objects.filter(person_id=person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()
        
    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600
    prob = kmf.predict(tempo_utente)

    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))
    kmf.plot_survival_function(ax=ax, ci_show=False, color='blue')
    ax.axhspan(0.6, 1, color='green', alpha=0.2)
    ax.axhspan(0.4, 0.6, color='yellow', alpha=0.2)
    ax.axhspan(0, 0.4, color='red', alpha=0.2)
    ax.scatter(tempo_utente, prob, color='blue', s=100, zorder=3, label=f"Utente")
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

       
    if tempoPrev is not None:
        tempoPrev = int(tempoPrev)
        prob = kmf.predict(tempo_utente+tempoPrev)
        ax.scatter(tempo_utente+tempoPrev, prob, color='yellow', s=100, zorder=3, label=f"Previsão")   
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')


    plt.title(f"Estatistico - Risco Clinico - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de não ocorrer um Evento")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def graphicPatientGlobal_rsf(person_id,tempoPrev=None):
    """
    @brief Gera gráfico de sobrevivência RSF global com destaque para o utente.
    @param person_id ID do utente.
    @return HttpResponse com imagem PNG.
    """
    import numpy as np
    from matplotlib import pyplot as plt
    from io import BytesIO


    rsf = get_global_model()
    if rsf is None:
        return HttpResponse("Modelo global RSF não encontrado", status=404)


    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    medicao = Measurement.objects.filter(person_id=person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()

    if not visita or not medicao:
        return HttpResponse("Dados de visita ou medição em falta", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600


    valor = medicao.value_as_number


    try:
        prob = np.interp(tempo_utente, rsf[0].x, rsf[0].y)
    except:
        prob = 0.0


    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.step(rsf[0].x, rsf[0].y, where="post", color='blue', label='Utente')

    ax.axhspan(0.6, 1, color='green', alpha=0.2)
    ax.axhspan(0.4, 0.6, color='yellow', alpha=0.2)
    ax.axhspan(0, 0.4, color='red', alpha=0.2)

    ax.scatter(tempo_utente, prob, color='blue', s=100, zorder=3, label=f"Utente")
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    if tempoPrev is not None:
        tempoPrev = int(tempoPrev)
        try:
            prob = np.interp(tempo_utente+tempoPrev, rsf[0].x, rsf[0].y)
        except:
            prob = 0.0
        
        ax.scatter(tempo_utente+tempoPrev, prob, color='yellow', s=100, zorder=3, label=f"Previsão")
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')


    plt.title(f"Aprendizagem Automática - Risco Clínico - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel("Probabilidade de não ocorrer um Evento")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')
