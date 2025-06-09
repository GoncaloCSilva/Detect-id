import csv
from django.contrib import messages
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from lifelines import KaplanMeierFitter
from utentes.hd_utils import getCSV, getCurrentModel, predict_survival, setCurrentModel, trainModels, get_global_model, get_model
from .models import *
from django.template import loader
from rest_framework.decorators import api_view
import matplotlib.pyplot as plt
from io import BytesIO, StringIO, TextIOWrapper
from .hd_graficos import graphicPatient_rsf, graphicPatientGlobal, graphicPatient_km, graphicPatientGlobal_rsf
from datetime import date, datetime
from decimal import Decimal
from django.utils import timezone
from .models import PersonExt, Measurement
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q




# Create your views here.
# IDs dos conceitos de medição (para a tabela dos utentes)
CONCEPT_IDS = {
    'spo2': 1,
    'o2': 2,
    'fc': 3,
    'tas': 4,
    'tad': 5,
    'temp': 6,
    'gcs': 7,
    'dor': 8,
}

def patients(request):
    """
    @brief: Page that lists all patients with their latest clinical measurements.

    @param request: HttpRequest object representing a GET request to view the patients ("utentes") page.
    @return: HttpResponse rendering the 'utentes.html' template with the paginated patient data, including measurement values and deterioration risk levels (current and predicted).
    """
    trainModels()
    
    patients = PersonExt.objects.all()
    patients_info = []
    time_prev = 24

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
        measurement = Measurement.objects.filter(person_id=patient.person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()
        
        time_patient = (measurement.measurement_datetime - visit.visit_start_datetime).total_seconds() / 3600

        global_model= get_global_model()

        global_risk = predict_survival(global_model, time_patient)
        global_risk_prev = predict_survival(global_model, time_patient + time_prev)

        if global_risk > 0.6: global_risk_measurements[patient.person_id] =  "Estável"
        elif global_risk > 0.4: global_risk_measurements[patient.person_id] =  "Moderado"
        else: global_risk_measurements[patient.person_id] =  "Emergência"

        if global_risk_prev > 0.6: global_risk_measurements_prev[patient.person_id] =  "Estável"
        elif global_risk_prev > 0.4: global_risk_measurements_prev[patient.person_id] =  "Moderado"
        else: global_risk_measurements_prev[patient.person_id] =  "Emergência"
    

        for key, concept_id in CONCEPT_IDS.items():
            measurement = (
                Measurement.objects
                .filter(person_id=patient.person_id, measurement_concept_id=concept_id)
                .order_by('-measurement_datetime')
                .first()
            )
            last_measurements[key] = measurement.value_as_number if measurement else None

            model = get_model(concept_id,measurement.value_as_number,1)
            prev = predict_survival(model, time_patient + time_prev)
            
            if prev > 0.6: prob_measurements[key] =  "Estável"
            elif prev > 0.4: prob_measurements[key] =  "Moderado"
            else: prob_measurements[key] =  "Emergência"

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
        'mymembers': page_obj,
        'temp_prev' : time_prev,
        'active_page': 'patients',
        'selected_model': selected_model
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

    patient = PersonExt.objects.get(person_id=person_id)
    condition = ConditionOccurrence.objects.get(person_id=person_id)
    age = patient.idade()
    event_filter = request.GET.get('evento')

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

        if global_risk > 0.6:
            grouped[dt]['risk'] = "Estável"
        elif global_risk > 0.4:
            grouped[dt]['risk'] = "Moderado"
        else:
            grouped[dt]['risk'] = "Emergência"

        grouped[dt]['measurements'].append(m)

    grouped = dict(sorted(grouped.items(), key=lambda item: item[0], reverse=True))

    service = VisitOccurrence.objects.filter(person_id=person_id)
    notes = Note.objects.filter(person_id=person_id)

    template = loader.get_template('utente.html')
    context = {
        'mymember': patient,
        'mycondition': condition,
        'idade': age,
        'grouped_measurements': grouped,
        'notes': notes,
        'servico': service,
        'event_filter':event_filter,
        'selected_model': selected_model
    }
    return HttpResponse(template.render(context, request))


def main(request):
  template = loader.get_template('main.html')
  return HttpResponse(template.render()) 

@csrf_exempt  # Desativa a verificação CSRF para esta view
def addPatient(request):
    """
    @brief: Handles the creation of a new patient and their associated clinical data.

    @param request: HttpRequest object representing a POST request with the patient's information.
    @return: Redirects to the patients listing page after successful insertion, or renders the 'adicionarUtente.html' template if GET request.
    """

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
        if request.POST.get("Serviço") == "Urgência": servico = 1 
        else: 
            if request.POST.get("Serviço") == "Internamento": servico = 2 
            else: servico = 3
        spO2 = request.POST.get("SpO2")
        o2 = request.POST.get("NecessidadeO2")
        heartRate = request.POST.get("FrequenciaCardiaca")
        tAS = request.POST.get("TASistolica")
        tAD = request.POST.get("TADiastolica")
        temperature = request.POST.get("Temperatura")
        gcs = request.POST.get("NívelConsciencia")
        pain = request.POST.get("Dor")

        date= date.today()
        dateTime=timezone.now()

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

        # Medições
        if spO2:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=1,  
                value_as_number=Decimal(spO2),
                measurement_datetime=dateTime
            )
        if o2:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=2, 
                value_as_number=int(o2),
                measurement_datetime=dateTime
            )
        if heartRate:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=3,  
                value_as_number=Decimal(heartRate),
                measurement_datetime=dateTime
            )
        
        if tAS:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=4,
                value_as_number=Decimal(tAS),
                measurement_datetime=dateTime
            )
        if tAD:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=5,  
                value_as_number=Decimal(tAD),
                measurement_datetime=dateTime
            )
        if temperature:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=6,  
                value_as_number=Decimal(temperature),
                measurement_datetime=dateTime
                )

        if gcs:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=7,  
                value_as_number=Decimal(gcs),
                measurement_datetime=dateTime
            )
        if pain:
            Measurement.objects.create(
                person=person,
                measurement_concept_id=8,  
                value_as_number=int(pain),
                measurement_datetime=dateTime
            )


        VisitOccurrence.objects.create(
            person=person,
            care_site_id=int(servico) if servico else 1, 
            visit_start_datetime=dateTime
        )
        

        return redirect("/utentes/")


    
    template = loader.get_template('adicionarUtente.html')
    context = {
        'active_page': 'addPatient'
    }

    return HttpResponse(template.render(context))       


def editPatient(request,person_id):
    """
    @brief: Handles the editing of an existing patient's personal information and the allows to add new measurements.

    @param request: HttpRequest object. Can be GET (to show the form) or POST (to save changes).
    @param person_id: ID of the patient to be edited.
    @return: Redirects to the patient list upon successful update, or renders the edit form if GET request.
    """
    patient = PersonExt.objects.get(person_id=person_id)
    if request.method == "POST":
        patient.first_name = request.POST.get("firstname")
        patient.last_name = request.POST.get("lastname")
        patient.birthday = request.POST.get("birthday")
        patient.gender_concept_id = request.POST.get("gender")
        patient.person_source_value = request.POST.get("NumeroUtente")
        patient.save()

        return redirect("/utentes/")
    
    return render(request, "editarUtente.html", {"utente": patient})

def newMeasurement(request, person_id):
    """
    @brief: Handles the creation of a new measurement for a specific patient
    @param request: HTTP request with POST data containing the measurement values
    @param person_id: The ID of the patient
    @return: Redirects to the patient's edit page after successful insertion.
    """
    if request.method == "POST":
        dateTime = datetime.now()

        Measurement.objects.create(person_id=person_id, measurement_concept_id=1, value_as_number=request.POST["spo2"], measurement_datetime=dateTime)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=2, value_as_number=request.POST["necessidade_o2"], measurement_datetime=dateTime)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=3, value_as_number=request.POST["fc"], measurement_datetime=dateTime)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=4, value_as_number=request.POST["ta_sistolica"], measurement_datetime=dateTime)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=5, value_as_number=request.POST["ta_diastolica"], measurement_datetime=dateTime)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=6, value_as_number=request.POST["temperatura"], measurement_datetime=dateTime)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=7, value_as_number=request.POST["nivel_consciencia"], measurement_datetime=dateTime)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=8, value_as_number=request.POST["dor"], measurement_datetime=dateTime)

    return redirect('editarUtente', person_id=person_id)


def removePatient(request, person_id):
    """
    @brief Handles the deletion of a patient and all related clinical records from the database.
    @param request: HTTP request object.
    @param person_id: ID of the patient to be removed.
    @return: Redirects to the patient list page after deletion.
    """

    patient = PersonExt.objects.get(person_id=person_id)

    if request.method == "POST":
        Measurement.objects.filter(person_id=person_id).delete()
        ConditionOccurrence.objects.filter(person_id=person_id).delete()
        Note.objects.filter(person_id=person_id).delete()
        Observation.objects.filter(person_id=person_id).delete()
        VisitOccurrence.objects.filter(person_id=person_id).delete()

        patient.delete()
        return redirect("/utentes/")

    return render(request, "details.html", {"mymember": patient})
  

def listPatients(request):
    """
    @brief Displays a paginated and optionally filtered list of patients with their latest clinical data and survival risk assessments.
    @param request: HTTP request containing optional filters (service, ordering, events, prediction time, search).
    @return: Renders the patient list page with relevant clinical and risk data.
    """

    service_filter = request.GET.get("service")
    order_by = request.GET.get("order")
    event_filter = request.GET.get("event")
    temp_prev = request.GET.get("temp_prev")
    search_query = request.GET.get('search')
    model = request.GET.get('model') 

    
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

    utentes = PersonExt.objects.all()

    if search_query:
        utentes = utentes.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    if not event_filter: event_filter = 1
    if not temp_prev: temp_prev = 24


    # Filter by service
    if service_filter in CARE_SITE_MAP.values():
        service_id = [k for k, v in CARE_SITE_MAP.items() if v == service_filter][0]
        person_ids = VisitOccurrence.objects.filter(
            care_site_id=service_id
        ).values_list("person_id", flat=True).distinct()
        utentes = utentes.filter(person_id__in=person_ids)

    # Order if needed
    if order_by in ["first_name", "-first_name", "last_name", "-last_name", "birthday", "-birthday"]:
        utentes = utentes.order_by(order_by)

   
    utentes_info = []
    for utente in utentes:
        last_measurements = {}
        prob_measurements = {}
        global_risk_measurements = {}
        global_risk_measurements_prev = {}

        # Tempo relativo do utente (em horas)
        visita = VisitOccurrence.objects.filter(person_id=utente.person_id).order_by('-visit_start_datetime').first()
        medicao = Measurement.objects.filter(person_id=utente.person_id, measurement_concept_id=1).order_by('-measurement_datetime').first()
        
        tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

        global_model= get_global_model()

        global_risk = predict_survival(global_model, tempo_utente)
        global_risk_prev = predict_survival(global_model,tempo_utente + int(temp_prev))

        if global_risk > 0.6: global_risk_measurements[utente.person_id] =  "Estável"
        elif global_risk > 0.4: global_risk_measurements[utente.person_id] =  "Moderado"
        else: global_risk_measurements[utente.person_id] =  "Emergência"

        if global_risk_prev > 0.6: global_risk_measurements_prev[utente.person_id] =  "Estável"
        elif global_risk_prev > 0.4: global_risk_measurements_prev[utente.person_id] =  "Moderado"
        else: global_risk_measurements_prev[utente.person_id] =  "Emergência"
    

        for key, concept_id in CONCEPT_IDS.items():
            measurement = (
                Measurement.objects
                .filter(person_id=utente.person_id, measurement_concept_id=concept_id)
                .order_by('-measurement_datetime')
                .first()
            )
            last_measurements[key] = measurement.value_as_number if measurement else None
            model = get_model(concept_id,measurement.value_as_number,int(event_filter))
            prev = predict_survival(global_model,tempo_utente + int(temp_prev))
            
            if prev > 0.6: prob_measurements[key] =  "Estável"
            elif prev > 0.4: prob_measurements[key] =  "Moderado"
            else: prob_measurements[key] =  "Emergência"

        utentes_info.append({
            'person': utente,
            **last_measurements,
            'prev' : prob_measurements,
            'global':global_risk_measurements,
            'global_prev':global_risk_measurements_prev
        })
    
    paginator = Paginator(utentes_info, 10)  
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    return render(request, "utentes.html", {
        "mymembers": page_obj,
        "service_filter": service_filter,
        "order_by": order_by,
        "event_filter": event_filter,
        "temp_prev":temp_prev,
        "search_query":search_query,
        'active_page': 'patients',
        'selected_model': selected_model
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
            df = getCSV(csv_file)

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

    # Usar buffer em memória
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=detectid_export.csv'
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

    if model == 'km':
        setCurrentModel(1)
        if parameter == "RC":
            return graphicPatientGlobal(person_id)
    
        return graphicPatient_km(person_id, parameter, event)
    elif model == 'rsf':
        setCurrentModel(2)
        if parameter == "RC":
            return graphicPatientGlobal_rsf(person_id)
    
        return graphicPatient_rsf(person_id, parameter, event)
    elif getCurrentModel() == 1:
        if parameter == "RC":
            return graphicPatientGlobal(person_id)
    
        return graphicPatient_km(person_id, parameter, event)
    else:
        if parameter == "RC":
            return graphicPatientGlobal_rsf(person_id)
    
        return graphicPatient_rsf(person_id, parameter, event)



  

