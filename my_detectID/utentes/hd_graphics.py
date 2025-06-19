import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import KaplanMeierFitter
from io import BytesIO
import matplotlib.pyplot as plt
from django.http import HttpResponse
import pandas as pd

from utentes.hd_utils import get_events, get_global_model, get_parameters, getLimiares, load_config, trainModels, get_model
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
    config = load_config()  
    general_settings = config['general_settings']
    graph_settings = config['graph_settings']

    thresholds_values = general_settings['thresholds_states']
    num_states = general_settings['num_states']
    name_states = general_settings['name_states']

    colors = graph_settings['graph_color_states']
    thresholds_colors = graph_settings['graph_color_thresholds']
    points_colors = graph_settings['graph_color_points']

    parameters = get_parameters()
    events = get_events()
    
    param_id = int(param_id)
    try:
        evento_id = int(evento_id)
    except:
        evento_id = 1  
        
    (name_param,abv_name,fullname,thresholds,unit) = parameters[param_id]
    event_name = events[evento_id]
    

    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=param_id)
        .order_by('-measurement_datetime')
        .first()
    )

    if not medicao:
        return HttpResponse(f"Medição de {name_param} não encontrada para este utente", status=404)

    valor = medicao.value_as_number
    group = num_states - 1
    for i in range(0, num_states-1):
        if valor >= thresholds[i]:
            group = i
            break

    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.axhspan(general_settings["thresholds_states"][0], 1, color=graph_settings["graph_color_states"][0], alpha=0.2)
    for i in range(1, general_settings['num_states']-1):
        ax.axhspan(general_settings["thresholds_states"][i], general_settings["thresholds_states"][i-1], color=graph_settings["graph_color_states"][i], alpha=0.2)
    ax.axhspan(0, general_settings["thresholds_states"][-1], color=graph_settings["graph_color_states"][-1], alpha=0.2)

    kmf = get_model(param_id,valor,evento_id)

    if param_id != 2:
        if group == 0: label_text=f"[{thresholds[0]}, \u221E["
        elif group == num_states - 1: label_text = f"[0,{thresholds[-1]}]"
        else: label_text = f"[{thresholds[group]},{thresholds[group-1]}["
    else:
        if group == 0: label_text = "Sim"
        else: label_text = "Não"

    kmf.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[group],label = label_text)
    
    for i in range(0, num_states-1):
        if i != group:

            if param_id == 2:
                if i == 0: label_text = "Sim"
                else: label_text = "Não"
            else:
                if i == 0: label_text=f"[{thresholds[0]}, \u221E["
                else:label_text = f"[{thresholds[i]},{thresholds[i-1]}["

            kmf2 = get_model(param_id,thresholds[i],evento_id)
            kmf2.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[i],label=label_text)
            if param_id==2 or param_id ==8 or param_id == 6:
                break
            
    
    if group != num_states - 1 and (param_id!=2 and param_id !=8 and param_id != 6):
        kmf3 = get_model(param_id,0,evento_id)
        kmf3.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[-1],label=f"[0,{thresholds[-1]}]")

           
    prob = kmf.predict(tempo_utente)
    ax.scatter(tempo_utente, prob, color=points_colors[0], s=100, zorder=3, label=f"Utente")   
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')
    
    if tempoPrev is not None:
        tempoPrev = float(tempoPrev)
        prob = kmf.predict(tempo_utente+tempoPrev)
        ax.scatter(tempo_utente+tempoPrev, prob,color=points_colors[1], s=100, zorder=3, label=f"Previsão")   
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    plt.title(f"Modelo Estatístico - {name_param} - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de estabilidade clinica")
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

    config = load_config()  
    general_settings = config['general_settings']
    graph_settings = config['graph_settings']

    thresholds_values = general_settings['thresholds_states']
    num_states = general_settings['num_states']
    name_states = general_settings['name_states']

    colors = graph_settings['graph_color_states']
    thresholds_colors = graph_settings['graph_color_thresholds']
    points_colors = graph_settings['graph_color_points']
    parameters = get_parameters()
    events = get_events()

    (name_param,abv_name,fullname,thresholds,unit) = parameters[param_id]
    event_name = events[evento_id]

    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=param_id)
        .order_by('-measurement_datetime')
        .first()
    )
    if not medicao:
        return HttpResponse(f"Medição de {name_param} não encontrada para este utente", status=404)

    valor = medicao.value_as_number
    group = num_states - 1
    for i in range(0, num_states-1):
        if valor >= thresholds[i]:
            group = i
            break


    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.axhspan(general_settings["thresholds_states"][0], 1, color=graph_settings["graph_color_states"][0], alpha=0.2)
    for i in range(1, general_settings['num_states']-1):
        ax.axhspan(general_settings["thresholds_states"][i], general_settings["thresholds_states"][i-1], color=graph_settings["graph_color_states"][i], alpha=0.2)
    ax.axhspan(0, general_settings["thresholds_states"][-1], color=graph_settings["graph_color_states"][-1], alpha=0.2)

    rsf = get_model(param_id,valor,evento_id)

    if param_id != 2:
        if group == 0: label_text=f"[{thresholds[0]}, \u221E["
        elif group == num_states - 1: label_text = f"[0,{thresholds[-1]}]"
        else: label_text = f"[{thresholds[group]},{thresholds[group-1]}["
    else:
        if group == 0: label_text = "Sim"
        else: label_text = "Não"

    ax.step(rsf[0].x, rsf[0].y, where="post", color=thresholds_colors[group], label=label_text)

    for i in range(0, num_states-1):
        if i != group:

            if param_id == 2:
                if i == 0: label_text = "Sim"
                else: label_text = "Não"
            else:
                if i == 0: label_text=f"[{thresholds[0]}, \u221E["
                else:label_text = f"[{thresholds[i]},{thresholds[i-1]}["

            rsf2 = get_model(param_id,thresholds[i],evento_id)
            ax.step(rsf2[0].x, rsf2[0].y, where="post", color=thresholds_colors[i], label=label_text)
            if param_id==2 or param_id ==8 or param_id == 6:
                break

    if group != num_states - 1 and (param_id!=2 and param_id !=8 and param_id != 6):
        rsf3 = get_model(param_id,0,evento_id)
        ax.step(rsf3[0].x, rsf3[0].y, where="post", color=thresholds_colors[-1], label=f"[0,{thresholds[-1]}]")

    try:
        prob = np.interp(tempo_utente, rsf[0].x, rsf[0].y)
    except:
        prob = 0.0

    ax.scatter(tempo_utente, prob, color=points_colors[0], s=100, zorder=3, label=f"Utente")
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    if tempoPrev is not None:
        tempoPrev = float(tempoPrev)
        try:
            prob = np.interp(tempo_utente+tempoPrev, rsf[0].x, rsf[0].y)
        except:
            prob = 0.0
        
        ax.scatter(tempo_utente+tempoPrev, prob, color=points_colors[1], s=100, zorder=3, label=f"Previsão")
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')


    plt.title(f"Aprendizagem Automática - {name_param} - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de estabilidade clinica")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')



def graphicPatientGlobal(person_id,tempoPrev=None):
    kmf = get_global_model()

    config = load_config()  
    general_settings = config['general_settings']
    graph_settings = config['graph_settings']

    thresholds_values = general_settings['thresholds_states']
    num_states = general_settings['num_states']
    name_states = general_settings['name_states']

    colors = graph_settings['graph_color_states']
    thresholds_colors = graph_settings['graph_color_thresholds']
    points_colors = graph_settings['graph_color_points']

    parameters = get_parameters()
    events = get_events()

    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    medicao = Measurement.objects.filter(person_id=person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()
        
    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600
    prob = kmf.predict(tempo_utente)

    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))
    kmf.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[0])
    ax.axhspan(general_settings["thresholds_states"][0], 1, color=graph_settings["graph_color_states"][0], alpha=0.2)
    for i in range(1, general_settings['num_states']-1):
        ax.axhspan(general_settings["thresholds_states"][i], general_settings["thresholds_states"][i-1], color=graph_settings["graph_color_states"][i], alpha=0.2)
    ax.axhspan(0, general_settings["thresholds_states"][-1], color=graph_settings["graph_color_states"][-1], alpha=0.2)

    ax.scatter(tempo_utente, prob, color=points_colors[0], s=100, zorder=3, label=f"Utente")
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

       
    if tempoPrev is not None:
        tempoPrev = float(tempoPrev)
        prob = kmf.predict(tempo_utente+tempoPrev)
        ax.scatter(tempo_utente+tempoPrev, prob, color=points_colors[1], s=100, zorder=3, label=f"Previsão")   
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')


    plt.title(f"Estatistico - Risco Clinico - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de estabilidade clinica")
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

    config = load_config()  
    general_settings = config['general_settings']
    graph_settings = config['graph_settings']

    thresholds_values = general_settings['thresholds_states']
    num_states = general_settings['num_states']
    name_states = general_settings['name_states']

    colors = graph_settings['graph_color_states']
    thresholds_colors = graph_settings['graph_color_thresholds']
    points_colors = graph_settings['graph_color_points']

    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    medicao = Measurement.objects.filter(person_id=person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600


    try:
        prob = np.interp(tempo_utente, rsf[0].x, rsf[0].y)
    except:
        prob = 0.0


    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.step(rsf[0].x, rsf[0].y, where="post", color=thresholds_colors[0], label='Utente')

    ax.axhspan(general_settings["thresholds_states"][0], 1, color=graph_settings["graph_color_states"][0], alpha=0.2)
    for i in range(1, general_settings['num_states']-1):
        ax.axhspan(general_settings["thresholds_states"][i], general_settings["thresholds_states"][i-1], color=graph_settings["graph_color_states"][i], alpha=0.2)
    ax.axhspan(0, general_settings["thresholds_states"][-1], color=graph_settings["graph_color_states"][-1], alpha=0.2)


    ax.scatter(tempo_utente, prob, color=points_colors[0], s=100, zorder=3, label=f"Utente")
    ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    if tempoPrev is not None:
        tempoPrev = float(tempoPrev)
        try:
            prob = np.interp(tempo_utente+tempoPrev, rsf[0].x, rsf[0].y)
        except:
            prob = 0.0
        
        ax.scatter(tempo_utente+tempoPrev, prob, color=points_colors[1], s=100, zorder=3, label=f"Previsão")
        ax.annotate(f"{prob:.2f}", (tempo_utente+tempoPrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')


    plt.title(f"Aprendizagem Automática - Risco Clínico - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel("Probabilidade de estabilidade clinica")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')
