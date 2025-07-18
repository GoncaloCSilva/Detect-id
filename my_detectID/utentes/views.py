from collections import defaultdict
import csv
from django.contrib import messages
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from utentes.hd_utils import changeCSV, get_parameters, load_config,get_events, getCurrentModel, predict_survival, setCurrentModel, trainModels, get_global_model, get_model
from .models import *
from django.template import loader
from .hd_graphics import graphicPatient, graphicPatientGlobal
from datetime import datetime
from decimal import Decimal
from .models import PersonExt, Measurement
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q

# Create your views here.
 
def patients(request):
    """
    @brief: Page that lists all patients with their latest clinical measurements.

    @param request: HttpRequest object representing a GET request to view the patients ("utentes") page.
    @return: HttpResponse rendering the 'utentes.html' template with the paginated patient data, including measurement values and deterioration risk levels (current and predicted).
    """
    trainModels()
    
    patients = PersonExt.objects.all().order_by('person_id')
    patients_info = []

    config = load_config()
    settings = config['general_settings']
    num_states = settings['num_states']
    thresholds_states = settings['thresholds_states']
    name_states = settings['name_states']
    hours = config['prediction_hours']
    time_prev = hours[0]
    events = get_events()
    event_filter = 1
    parameters = get_parameters()

    states = {}
    for i in range(0, num_states):
        states[i] = {
            'name': name_states[i],
            'id': i
        }
    
    eventsDict = {}
    for i in range(1, len(events)+1):
        eventsDict[i] = {
            'name': events[i],
            'id': i
        }

    if getCurrentModel() == 1:
        selected_model = 'km'   
    else:
        selected_model = 'rsf'
    
    # For each patient, retrieve the latest measurement of each clinical parameter,
    # estimate deterioration risk using survival models,
    # and store everything in `patients_info` for display on the "Utentes" page.

    for patient in patients:
        last_measurements = {}
        prob_measurements = {}
        global_risk_measurements = {}
        global_risk_measurements_prev = {}

        # Time relative to patient (in hours)
        visit = VisitOccurrence.objects.filter(person_id=patient.person_id).order_by('-visit_start_datetime').first()
        visit_end = VisitOccurrence.objects.filter(person_id=patient.person_id,visit_end_datetime__isnull=False).exists()
        if  not visit_end:
            measurement = Measurement.objects.filter(person_id=patient.person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()
            
            time_patient = (measurement.measurement_datetime - visit.visit_start_datetime).total_seconds() / 3600

            global_model= get_global_model()

            
            if getCurrentModel() == 1:
                if patient.probability_km is not None:
                    global_risk = patient.probability_km
                else:
                    global_risk = predict_survival(global_model, time_patient)
                    patient.probability_km = global_risk
                    patient.save()
            else:
                if patient.probability_rsf is not None:
                    global_risk = patient.probability_rsf
                else:
                    global_risk = predict_survival(global_model, time_patient)
                    patient.probability_rsf = global_risk
                    patient.save()
            
            global_risk_prev = predict_survival(global_model, time_patient + time_prev)

            check = False
            for i in range(0, num_states - 1):
                if global_risk >= thresholds_states[i]:
                    global_risk_measurements[patient.person_id] =  i + 1
                    global_risk_measurements["Name"] = name_states[i]
                    check = True
                    break
            if check is False:
                global_risk_measurements[patient.person_id] =  num_states 
                global_risk_measurements["Name"] = name_states[-1]

            check = False    
            for i in range(0, num_states - 1):
                if global_risk_prev >= thresholds_states[i]:
                    global_risk_measurements_prev[patient.person_id] =  i + 1
                    global_risk_measurements_prev["Name"] = name_states[i]      
                    check = True
                    break
            if check is False:
                global_risk_measurements_prev[patient.person_id] =  num_states        
                global_risk_measurements_prev["Name"] = name_states[-1]   
        
            for parameter_id,(name,abv_name,full_name,thresholds,unit) in parameters.items():
                measurement = (
                    Measurement.objects
                    .filter(person_id=patient.person_id, measurement_concept_id=parameter_id)
                    .order_by('-measurement_datetime')
                    .first()
                )

                last_measurements[parameter_id] = measurement.value_as_number
                model = get_model(parameter_id,measurement.value_as_number,1)
                prev = predict_survival(model, time_patient + time_prev)
               
                check = False
                for i in range(0, num_states - 1):
                    if prev >= thresholds_states[i]:
                        prob_measurements[parameter_id] =  i + 1
                        check = True
                        break
                if check is False:
                    prob_measurements[parameter_id] =  num_states    
       

            patients_info.append({
                'person': patient,
                **last_measurements,
                'prev' : prob_measurements,
                'global':global_risk_measurements,
                'global_prev':global_risk_measurements_prev
            })


    paginator = Paginator(patients_info, 10)  
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    
    return render(request, 'utentes.html', {
        'patients': page_obj,
        'time_prev' : time_prev,
        'active_page': 'patients',
        'selected_model': selected_model,
        'hours': hours,
        'states': states,
        'events': eventsDict,
        'event_filter': event_filter,
        'parameters': parameters,
        'num_params': list(range(1, len(parameters.items()) + 1)),
    })

def patient(request, person_id):
    """
    @brief: View that returns the details page for a specific patient (utente), including personal data,
            clinical condition, measurement history, clinical notes, and hospitalization records.
    @param request: HTTP request (GET)
    @param person_id: Unique identifier of the patient (utente)
    @return: Renders the 'utente.html' template with the corresponding patient data
    """
    model = request.GET.get('model') 

    config = load_config()
    settings = config['general_settings']
    num_states = settings['num_states']
    thresholds_states = settings['thresholds_states']
    name_states = settings['name_states']
    events = get_events()
    parameters = get_parameters()


    states = {}
    for i in range(0, num_states):
        states[i] = {
            'name': name_states[i],
            'id': i
        }
    
    eventsDict = {}
    for i in range(1, len(events)+1):
        eventsDict[i] = {
            'name': events[i],
            'id': i
        }

    patient = PersonExt.objects.get(person_id=person_id)
    
    if model == 'km':
        setCurrentModel(1)
        selected_model = 'km'
    elif model == 'rsf':
        setCurrentModel(2)
        selected_model = 'rsf'
    elif getCurrentModel() == 1:
        selected_model = 'km'
    else:
        selected_model = 'rsf'
    
    global_model= get_global_model()

    condition = ConditionOccurrence.objects.get(person_id=person_id)
    age = patient.idade()
    event_filter = request.GET.get('evento',1)

    # Agrupar medições por data e hora
    measurements = Measurement.objects.filter(person_id=person_id)
    grouped = {}
    for m in measurements:
        dt = m.measurement_datetime

        # Cálculo de tempo do utente
        visit = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
        time_patient = (dt - visit.visit_start_datetime).total_seconds() / 3600

        global_risk = predict_survival(global_model, time_patient)
        if dt not in grouped:
            grouped[dt] = {
                'risk': '', 
                'measurements': []
            }

        check = False
        for i in range(0, num_states - 1):
            if global_risk >= thresholds_states[i]:
                grouped[dt]['risk'] =  i + 1
                grouped[dt]['Name'] = name_states[i]
                check = True
                break
        if check is False:
            grouped[dt]['risk'] =  num_states 
            grouped[dt]['Name'] = name_states[-1]

        grouped[dt]['measurements'].append(m)

    grouped = dict(sorted(grouped.items(), key=lambda item: item[0], reverse=True))

    service = VisitOccurrence.objects.filter(person_id=person_id)
    notes = Note.objects.filter(person_id=person_id)
    # Filtrar observações da pessoa
    observacoes = Observation.objects.filter(person_id=person_id).order_by('-observation_datetime')

    # Agrupar por timestamp e juntar os eventos (usando defaultdict para lista)
    eventos_por_data = defaultdict(list)
    for obs in observacoes:
        data_hora = obs.observation_datetime
        evento = events[obs.observation_concept_id]
        eventos_por_data[data_hora].append(evento)

    # Reorganizar como lista de dicionários para usar no template
    eventos = [
        {"timestamp": data, "lista_eventos": eventos_por_data[data]}
        for data in sorted(eventos_por_data.keys(), reverse=True)
    ]


    template = loader.get_template('utente.html')
    context = {
        'eventos': eventos,
        'mymember': patient,
        'mycondition': condition,
        'idade': age,
        'grouped_measurements': grouped,
        'notes': notes,
        'servico': service,
        'event_filter':event_filter,
        'selected_model': selected_model,
        'events': eventsDict,
        'parameters': parameters,
        'num_params': list(range(1, len(parameters.items()) + 1)),
        
    }
    return HttpResponse(template.render(context, request))

def main(request):
  template = loader.get_template('main.html')
  return HttpResponse(template.render()) 


def addPatient(request):
    """
    @brief: Handles the creation of a new patient and their associated clinical data.

    @param request: HttpRequest object representing a POST request with the patient's information.
    @return: Redirects to the patients listing page after successful insertion, or renders the 'adicionarUtente.html' template if GET request.
    """
    parameters = get_parameters()
    if request.method == "POST":

        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        birthday = request.POST.get("birthday")
        if request.POST.get("gender") == "Male": gender = 1 
        else: gender = 0
        numeroUtente = request.POST.get("NumeroUtente")
        queixasEntrada = request.POST.get("QueixasEntrada")
        alergies = request.POST.get("Alergias")
        diagnosis = request.POST.get("DiagnosticoPrincipal")
        if request.POST.get("Serviço") == "Urgência": service = 1 
        else: 
            if request.POST.get("Serviço") == "Internamento": service = 2 
            else: service = 3

        dateTime=datetime.now()
        date = dateTime.date()
        person = PersonExt.objects.create(
            gender_concept_id=int(gender),
            person_source_value=numeroUtente,
            birthday=birthday,
            first_name=firstname,
            last_name=lastname
        )

        # Condição principal
        ConditionOccurrence.objects.create(
            person=person,
            condition_start_date=date,
            condition_source_value=diagnosis
        )

        # Notas (Queixas e Alergias)
        if queixasEntrada:
            Note.objects.create(
                person=person,
                note_text=queixasEntrada,
                note_type_concept_id=1  
            )
        if alergies:
            Note.objects.create(
                person=person,
                note_text=alergies,
                note_type_concept_id=2  
            )
        value = None
        for id, (name, abv_name, full_name, thresholds, unit) in parameters.items():
            value = request.POST.get(str(id))
            if value is not None:
                Measurement.objects.create(
                    person_id=person.person_id,
                    measurement_concept_id=id,
                    value_as_number=Decimal(value),
                    measurement_datetime=dateTime,
                    range_low=thresholds[0],
                    range_high=thresholds[1]
                )
        VisitOccurrence.objects.create(
            person=person,
            care_site_id=CareSite.objects.get(care_site_id=int(service) if service else 1).care_site_id, 
            visit_start_datetime=dateTime
        )
        

        return redirect("/utentes/")


    

    return render(request, 'adicionarUtente.html', {
        'active_page': 'addPatient',
        'parameters': parameters,
    })    


def editPatient(request,person_id):
    """
    @brief: Handles the editing of an existing patient's personal information and the allows to add new measurements.

    @param request: HttpRequest object. Can be GET (to show the form) or POST (to save changes).
    @param person_id: ID of the patient to be edited.
    @return: Redirects to the patient list upon successful update, or renders the edit form if GET request.
    """
    patient = PersonExt.objects.get(person_id=person_id)
    visit = VisitOccurrence.objects.get(person=patient)
    parameters = get_parameters() 

    
    if request.method == "POST":
        patient.first_name = request.POST.get("firstname")
        patient.last_name = request.POST.get("lastname")
        patient.birthday = request.POST.get("birthday")
        patient.gender_concept_id = request.POST.get("gender")
        patient.person_source_value = request.POST.get("NumeroUtente")
        service = VisitOccurrence.objects.get(person_id=person_id)
        service.care_site = CareSite.objects.get(care_site_id = int(request.POST.get("service")))
        service.save()
        patient.save()

        return redirect('patient', person_id=person_id)
    
    context = {
        'patient': patient,
        'visit': visit,
        'parameters': parameters,
        'active_page': 'editPatient'
    }
    return render(request, 'editarUtente.html', context)


def registEvent(request,person_id):
    """
    @brief: Handles the editing of an existing patient's personal information and the allows to add new measurements.

    @param request: HttpRequest object. Can be GET (to show the form) or POST (to save changes).
    @param person_id: ID of the patient to be edited.
    @return: Redirects to the patient list upon successful update, or renders the edit form if GET request.
    """
    parameters = get_parameters()
    person = PersonExt.objects.get(person_id=person_id)

    if request.method == "POST":
        dateTime = datetime.now()
        for id, (name, abv_name, full_name, thresholds, unit) in parameters.items():
            value = request.POST.get(str(id))
            if value is not None:
                Measurement.objects.create(
                    person_id=person.person_id,
                    measurement_concept_id=id,
                    value_as_number=Decimal(value),
                    measurement_datetime=dateTime,
                    range_low=thresholds[0],
                    range_high=thresholds[1]
                )
        eventos_selecionados = request.POST.getlist('eventos')
        for evento in eventos_selecionados:
            Observation.objects.create(
                person_id=person_id,
                observation_concept_id=int(evento),
                observation_datetime=dateTime
            )



        return redirect('patient', person_id=person_id)
    
    return render(request, "registarEvento.html", {"utente": person})


def newMeasurement(request, person_id):
    """
    @brief: Handles the creation of a new measurement for a specific patient
    @param request: HTTP request with POST data containing the measurement values
    @param person_id: The ID of the patient
    @return: Redirects to the patient's edit page after successful insertion.
    """
    parameters = get_parameters()
    if request.method == "POST":
        dateTime = datetime.now()

        for id, (name, abv_name, full_name, thresholds, unit) in parameters.items():
            value = request.POST.get(str(id))
            if value is not None:
                numeric_value = abs(Decimal(value))
                Measurement.objects.create(
                    person_id=person_id,
                    measurement_concept_id=id,
                    value_as_number=numeric_value,
                    measurement_datetime=dateTime,
                    range_low=thresholds[0],
                    range_high=thresholds[1]
                )
    return redirect('patient', person_id=person_id)

def removePatient(request, person_id):
    """
    @brief Handles the deletion of a patient and all related clinical records from the database.
    @param request: HTTP request object.
    @param person_id: ID of the patient to be removed.
    @return: Redirects to the patient list page after deletion.
    """

    patient = PersonExt.objects.get(person_id=person_id)

    if request.method == "POST":
        dateTime = datetime.now()
        visit = VisitOccurrence.objects.filter(person_id=person_id).last()
        visit.visit_end_datetime = dateTime
        visit.save()
        return redirect("/utentes/")

    return render(request, "details.html", {"mymember": patient})
  
def listPatients(request):
    """
    @brief Displays a paginated and optionally filtered list of patients with their latest clinical data and survival risk assessments.
    @param request: HTTP request containing optional filters (service, ordering, events, prediction time, search).
    @return: Renders the patient list page with relevant clinical and risk data.
    """

    service_filter = request.GET.get("service")
    state_filter = request.GET.get("stateSelect")
    order_by = request.GET.get("order")
    event_filter = request.GET.get("event")
    time_prev = request.GET.get("time_prev")
    search_query = request.GET.get('search')
    model = request.GET.get('model') 
    alert = request.GET.get('alert')

    config = load_config()
    settings = config['general_settings']
    num_states = settings['num_states']
    thresholds_states = settings['thresholds_states']
    name_states = settings['name_states']
    hours = config['prediction_hours']
    events = get_events()
    parameters = get_parameters()

    states = {}
    for i in range(0, num_states):
        states[i] = {
            'name': name_states[i],
            'id': i
        }

    eventsDict = {}
    for i in range(1, len(events)+1):
        eventsDict[i] = {
            'name': events[i],
            'id': i
        }

    if model == 'km':
        setCurrentModel(1)
        selected_model = 'km'
    elif model == 'rsf':
        setCurrentModel(2)
        selected_model = 'rsf'
    elif getCurrentModel() == 1:
        selected_model = 'km'
    else:
        selected_model = 'rsf'

    CARE_SITE_MAP = {
        1: "Urgência",                      
        2: "Internamento",
        3: "UCI",
    }

    utentes = PersonExt.objects.all().order_by('person_id')

    if search_query:
        search_terms = search_query.strip().split()
        for term in search_terms:
            utentes = utentes.filter(
                Q(first_name__icontains=term) | 
                Q(last_name__icontains=term)
            )

    # Filter by service
    if service_filter in CARE_SITE_MAP.values():
        service_id = [k for k, v in CARE_SITE_MAP.items() if v == service_filter][0]
        person_ids = VisitOccurrence.objects.filter(
            care_site_id=service_id
        ).values_list("person_id", flat=True).distinct()
        utentes = utentes.filter(person_id__in=person_ids)


    for i in range(0,num_states):
        if state_filter == str(states[i]['id']):
            if i == 0:
                utentes = utentes.filter(probability_km__gte=thresholds_states[0]) if getCurrentModel() == 1 else utentes.filter(probability_rsf__gte=thresholds_states[0])
            elif i == num_states-1:
                utentes = utentes.filter(probability_km__lt=thresholds_states[-1]) if getCurrentModel() == 1 else utentes.filter(probability_rsf__lt=thresholds_states[-1])
            else:
                utentes = utentes.filter(probability_km__gte=thresholds_states[i], probability_km__lt=thresholds_states[i-1]) if getCurrentModel() == 1 else utentes.filter(probability_rsf__gte=thresholds_states[i], probability_rsf__lt=thresholds_states[i-1])
        
    # Order if needed
    if order_by in ["first_name", "-first_name", "last_name", "-last_name", "birthday", "-birthday"]:
        utentes = utentes.order_by(order_by)

    utentes_info = []
    for patient in utentes:

        last_measurements = {}
        prob_measurements = {}
        global_risk_measurements = {}
        global_risk_measurements_prev = {}

        visita = VisitOccurrence.objects.filter(person_id=patient.person_id).order_by('-visit_start_datetime').first()
        visit_end = VisitOccurrence.objects.filter(person_id=patient.person_id,visit_end_datetime__isnull=False).exists()
        if not visit_end:
            medicao = Measurement.objects.filter(person_id=patient.person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()
            
            time_patient = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

            global_model= get_global_model()

            global_risk_prev = predict_survival(global_model,time_patient +float(time_prev))

            if getCurrentModel() == 1:
                if patient.probability_km is not None:
                    global_risk = patient.probability_km
                else:
                    global_risk = predict_survival(global_model, time_patient)
                    patient.probability_km = global_risk
                    patient.save()
            else:
                if patient.probability_rsf is not None:
                    global_risk = patient.probability_rsf
                else:
                    global_risk = predict_survival(global_model, time_patient)
                    patient.probability_rsf = global_risk
                    patient.save()

            check = False
            for i in range(0, num_states - 1):
                if global_risk >= thresholds_states[i]:
                    global_risk_measurement_id =  i + 1
                    global_risk_measurement_name = name_states[i]
                    check = True
                    break
            if check is False:
                global_risk_measurement_id =  num_states 
                global_risk_measurement_name = name_states[-1]

            check = False    
            for i in range(0, num_states - 1):
                if global_risk_prev >= thresholds_states[i]:
                    global_risk_measurements_prev_id =  i + 1
                    global_risk_measurements_prev_name = name_states[i]      
                    check = True
                    break
            if check is False:
                global_risk_measurements_prev_id =  num_states        
                global_risk_measurements_prev_name = name_states[-1]

            if alert == "1":
                if global_risk_measurements_prev_name == global_risk_measurement_name:
                    continue

            global_risk_measurements[patient.person_id] =  global_risk_measurement_id
            global_risk_measurements["Name"] = global_risk_measurement_name
            global_risk_measurements_prev[patient.person_id] =  global_risk_measurements_prev_id
            global_risk_measurements_prev["Name"] = global_risk_measurements_prev_name
            
            for parameter_id,(name,abv_name,full_name,thresholds,unit) in parameters.items():
                measurement = (
                    Measurement.objects
                    .filter(person_id=patient.person_id, measurement_concept_id=parameter_id)
                    .order_by('-measurement_datetime')
                    .first()
                )
                last_measurements[parameter_id] = measurement.value_as_number 
                model = get_model(parameter_id,measurement.value_as_number,int(event_filter))
                prev = predict_survival(model,time_patient + float(time_prev))
               
                check = False
                for i in range(0, num_states - 1):
                    if prev >= thresholds_states[i]:
                        prob_measurements[parameter_id] =  i + 1
                        check = True
                        break
                if check is False:
                    prob_measurements[parameter_id] =  num_states    

            utentes_info.append({
                'person': patient,
                **last_measurements,
                'prev' : prob_measurements,
                'global':global_risk_measurements,
                'global_prev':global_risk_measurements_prev
            })
    
    paginator = Paginator(utentes_info, 10)  
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    return render(request, "utentes.html", {
        "patients": page_obj,
        "service_filter": service_filter,
        "state_filter":state_filter,
        "order_by": order_by,
        "event_filter": event_filter,
        "time_prev":time_prev,
        "search_query":search_query,
        'active_page': 'patients',
        'selected_model': selected_model,
        'hours': hours,
        'states': states,
        'events': eventsDict,
        'parameters': parameters,
        'alert_filter': alert,
        'num_params': list(range(1, len(parameters.items()) + 1)),
    })

@csrf_exempt
def importCSV(request):
    """
    @brief Handles the import of a CSV file uploaded via POST request and displays a success or error message.
    @param request: HTTP request object, expects a file under 'csv_file' in POST data.
    @return: Renders the main page with a status message.
    """
    if request.method == "POST":
        try:
            csv_file = request.FILES["csv_file"]
            changeCSV(csv_file)
            messages.success(request, "✅ Ficheiro importado com sucesso!")
        except Exception as e:
            messages.error(request, f"❌ Erro ao importar: {e}")
        return render(request, 'main.html')
    
    return render(request, 'main.html')

def exportCSV(request):
    """
    @brief Generates and returns a CSV file containing the output of the Kaplan-Meier training results.
    @param request: HTTP request object.
    @return: HTTP response with CSV file attached for download.
    """

    df = trainModels()

    filename = "exported_data.csv"
    parameters = get_parameters()
    events = get_events()

    fieldnames = [
        "Pessoa","Primeiro Nome", "Último Nome", "Número de Utente",
        "Genero", "Data de Nascimento", "Diagnóstico Principal",
        "Queixas de Entrada", "Alergias",
        "Serviço", "Data/Hora de Entrada", "Data/Hora de Saída",
        "Dia de Medição", "Hora de Medição"] + [v[0] for v in parameters.values()] + [v for v in events.values()] + ["Evento"]

    # Create CSV File
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        pessoas = {p.person_id: p for p in PersonExt.objects.all()}

        medidas = Measurement.objects.all().order_by("person_id", "measurement_datetime")
        medidas_por_pessoa = {}
        for m in medidas:
            chave = (m.person_id, m.measurement_datetime)
            if chave not in medidas_por_pessoa:
                medidas_por_pessoa[chave] = {}
            medidas_por_pessoa[chave][m.measurement_concept_id] = m.value_as_number

        for (person_id, dt), medidas_dict in medidas_por_pessoa.items():
            pessoa = pessoas.get(person_id)
            if not pessoa:
                continue  
            try:
               alergias= Note.objects.filter(note_type_concept_id = 2).get(person=pessoa).note_text
            except:
                alergias =""

            try:
                alta = f"{VisitOccurrence.objects.get(person=pessoa).visit_end_datetime.date()} {VisitOccurrence.objects.get(person=pessoa).visit_end_datetime.time()}"
            except:
                alta= ""

            if pessoa.gender_concept_id == 1: gender = "Masculino"
            else: gender ="Feminino"

            row = {
                "Pessoa": pessoa.person_id,
                "Primeiro Nome": pessoa.first_name,
                "Último Nome": pessoa.last_name,
                "Número de Utente": pessoa.person_source_value,
                "Genero": gender,
                "Data de Nascimento": pessoa.birthday.strftime("%d/%m/%Y") if pessoa.birthday else "",
                "Diagnóstico Principal": ConditionOccurrence.objects.filter(person=pessoa).first().condition_source_value if ConditionOccurrence.objects.filter(person=pessoa).exists() else "",
                "Queixas de Entrada": Note.objects.filter(person=pessoa, note_type_concept_id=1).first().note_text if Note.objects.filter(person=pessoa, note_type_concept_id=1).exists() else "",
                "Alergias": alergias,
                "Serviço": CareSite.objects.get(
                    care_site_id=VisitOccurrence.objects.get(person=pessoa).care_site.care_site_id
                ).care_site_id if VisitOccurrence.objects.filter(person=pessoa).exists() else 1,
                "Data/Hora de Entrada": VisitOccurrence.objects.get(person=pessoa).visit_start_datetime.strftime("%d/%m/%Y %H:%M") if VisitOccurrence.objects.filter(person=pessoa).exists() else "",
                "Data/Hora de Saída": alta.strftime("%d/%m/%Y %H:%M") if isinstance(alta, datetime) else "",
                "Dia de Medição": dt.strftime("%d/%m/%Y") if dt else "",
                "Hora de Medição": dt.strftime("%H:%M") if dt else ""
            }

            for concept_name, param_data in parameters.items():
                name = param_data[0]
                row[name] = medidas_dict.get(concept_name, "")

            evento = 0
            for event_id, event_name in events.items():
                obs = Observation.objects.filter(
                    person=pessoa,
                    observation_concept_id=event_id,
                    observation_datetime=dt
                ).first()
                if obs:
                    try:
                        row[event_name] = int(obs.value_as_number)
                        evento = 1
                    except:
                        row[event_name] = 0
                else:
                    row[event_name] = 0
            
            row["Evento"] = evento
            writer.writerow(row)

    print(f"Exportação concluída: {filename}")

    with open(filename, "r", encoding="utf-8") as f:
        response = HttpResponse(f.read(), content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'
        return response

def graphicView(request, person_id):
    """
    @brief Selects and renders the appropriate survival chart for a given patient based on the selected parameter and event.
    @param request: HTTP request object containing 'parametro' and 'evento' in GET parameters.
    @param person_id: ID of the patient for whom the chart is generated.
    @return: HTTP response with the rendered chart (global or individual).
    """

    parameter = request.GET.get("parametro")  
    event = request.GET.get("evento")
    model = request.GET.get('model')
    time_prev = request.GET.get("time_prev",None)

    if model == 'km':
        setCurrentModel(1)
    else:
        setCurrentModel(2)

    if parameter == "RC":
        return graphicPatientGlobal(person_id, time_prev)
    else:
        return graphicPatient(person_id,parameter,event,time_prev)



  

