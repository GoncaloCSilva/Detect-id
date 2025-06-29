from io import BytesIO
import matplotlib.pyplot as plt
from django.http import HttpResponse
from matplotlib import pyplot as plt
from io import BytesIO

import numpy as np
from utentes.hd_utils import get_global_model, get_parameters, getCurrentModel, load_config, get_model
from .models import Measurement, PersonExt, VisitOccurrence

def graphicPatient(person_id,param_id,event_id,timePrev = None):
    """
    @brief Generates and returns a clinical stability survival plot for a given patient.
    
    Checks which model is being used and returns the plot for the given person, parameter, event and model

    @param person_id: ID of the patient (int)
    @param param_id: Clinical parameter/concept ID (int or str convertible to int)
    @param event_id: Event ID (int or str convertible to int, defaults to 1 if invalid)
    @param timePrev: Optional prediction horizon in hours (float)

    @return: HttpResponse containing the plot image (PNG format)
    """

    param_id = int(param_id)
    try:
        event_id = int(event_id)
    except:
        event_id = 1  

    config = load_config()  
    general_settings = config['general_settings']
    graph_settings = config['graph_settings']

    num_states = general_settings['num_states']

    thresholds_colors = graph_settings['graph_color_thresholds']
    points_colors = graph_settings['graph_color_points']

    parameters = get_parameters()
        
    (name_param,abv_name,fullname,thresholds,unit) = parameters[param_id]
    
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

    timePatient = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.axhspan(general_settings["thresholds_states"][0], 1, color=graph_settings["graph_color_states"][0], alpha=0.2)
    for i in range(1, general_settings['num_states']-1):
        ax.axhspan(general_settings["thresholds_states"][i], general_settings["thresholds_states"][i-1], color=graph_settings["graph_color_states"][i], alpha=0.2)
    ax.axhspan(0, general_settings["thresholds_states"][-1], color=graph_settings["graph_color_states"][-1], alpha=0.2)

    model = get_model(param_id,valor,event_id)

    if param_id == 2 or param_id == 8:
        if group == 0: label_text = "Sim"
        else: label_text = "Não"
    else:
        if group == 0: label_text=f"[{thresholds[0]}, \u221E["
        elif group == num_states - 1: label_text = f"[0,{thresholds[-1]}]"
        else: label_text = f"[{thresholds[group]},{thresholds[group-1]}["
        

    current_model = getCurrentModel()

    if current_model == 1:
        model.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[group],label = label_text)
        prob = model.predict(timePatient)
        title = "Modelo Estatístico"
    else:
        ax.step(model[0].x, model[0].y, where="post", color=thresholds_colors[group], label=label_text)
        title = "Aprendizagem Automática"
        try:
            prob = np.interp(timePatient, model[0].x, model[0].y)
        except:
            prob = 0.0


    for i in range(0, num_states-1):
        if i != group:

            if param_id == 2 or param_id == 8:
                if i == 0: label_text = "Sim"
                else: label_text = "Não"
            else:
                if i == 0: label_text=f"[{thresholds[0]}, \u221E["
                else:label_text = f"[{thresholds[i]},{thresholds[i-1]}["

            model2 = get_model(param_id,thresholds[i],event_id)

            if current_model == 1:
                model2.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[i], label=label_text)
            else:
                ax.step(model2[0].x, model2[0].y, where="post",color=thresholds_colors[i], label=label_text)

            if param_id==2 or param_id ==8:
                break
            
    
    if group != num_states - 1 and (param_id!=2 and param_id !=8):
        model3 = get_model(param_id,0,event_id)
        if current_model == 1:
            model3.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[-1],label=f"[0,{thresholds[-1]}]")
        else:
            ax.step(model3[0].x, model3[0].y, where="post", color=thresholds_colors[-1], label=f"[0,{thresholds[-1]}]")
    

    ax.scatter(timePatient, prob, color=points_colors[0], s=100, zorder=3, label=f"Utente")   
    ax.annotate(f"{prob:.2f}", (timePatient, prob), textcoords="offset points", xytext=(-10, -10), ha='center')
    
    if timePrev is not None:
        timePrev = float(timePrev)
        if current_model == 1:
            prob = model.predict(timePatient+timePrev)        
        else:
            try:
                prob = np.interp(timePatient+timePrev, model[0].x, model[0].y)
            except:
                prob = 0.0
        ax.scatter(timePatient+timePrev, prob,color=points_colors[1], s=100, zorder=3, label=f"Previsão")   
        ax.annotate(f"{prob:.2f}", (timePatient+timePrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    plt.title(f"{title} - {name_param} - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de estabilidade clinica")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')
    
def graphicPatientGlobal(person_id,timePrev=None):
    """
    @brief Generates and returns a clinical stability survival plot for a given patient.
    
    Checks which model is being used and returns the plot for the given person.

    @param person_id: ID of the patient (int)
    @param timePrev: Optional prediction horizon in hours (float)

    @return: HttpResponse containing the plot image (PNG format)
    """
    model = get_global_model()

    config = load_config()  
    general_settings = config['general_settings']
    graph_settings = config['graph_settings']

    thresholds_colors = graph_settings['graph_color_thresholds']
    points_colors = graph_settings['graph_color_points']

    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    medicao = Measurement.objects.filter(person_id=person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()
        
    timePatient = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))

    if getCurrentModel() == 1:
       prob = model.predict(timePatient)
       model.plot_survival_function(ax=ax, ci_show=False, color=thresholds_colors[0])
       title = "Estatístico"
    else:
        try:
            prob = np.interp(timePatient, model[0].x, model[0].y)
        except:
            prob = 0.0
        ax.step(model[0].x, model[0].y, where="post", color=thresholds_colors[0], label='Utente')
        title = "Aprendizagem Automática"

    
    ax.axhspan(general_settings["thresholds_states"][0], 1, color=graph_settings["graph_color_states"][0], alpha=0.2)
    for i in range(1, general_settings['num_states']-1):
        ax.axhspan(general_settings["thresholds_states"][i], general_settings["thresholds_states"][i-1], color=graph_settings["graph_color_states"][i], alpha=0.2)
    ax.axhspan(0, general_settings["thresholds_states"][-1], color=graph_settings["graph_color_states"][-1], alpha=0.2)

    ax.scatter(timePatient, prob, color=points_colors[0], s=100, zorder=3, label=f"Utente")
    ax.annotate(f"{prob:.2f}", (timePatient, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

       
    if timePrev is not None:
        timePrev = float(timePrev)
        if getCurrentModel() == 1:
            prob = model.predict(timePatient+timePrev)        
        else:
            try:
                prob = np.interp(timePatient+timePrev, model[0].x, model[0].y)
            except:
                prob = 0.0
        ax.scatter(timePatient+timePrev, prob,color=points_colors[1], s=100, zorder=3, label=f"Previsão")   
        ax.annotate(f"{prob:.2f}", (timePatient+timePrev, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    plt.title(f"{title} - Risco Clinico - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de estabilidade clinica")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)
    plt.legend()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')

