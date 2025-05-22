import csv
from django.contrib import messages
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from lifelines import KaplanMeierFitter
from utentes.hd_utils import getCSV, trainKM, get_global_kaplan_model, get_kaplan_model
from .models import *
from django.template import loader
from rest_framework.decorators import api_view
import matplotlib.pyplot as plt
from io import BytesIO, StringIO, TextIOWrapper
from .hd_graficos import grafico_global, grafico_individual
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

def utentes(request):
    """
    @brief: Page that lists all patients with their latest clinical measurements.

    @param request: HttpRequest object representing a GET request to view the patients ("utentes") page.
    @return: HttpResponse rendering the 'utentes.html' template with the paginated patient data, including measurement values and deterioration risk levels (current and predicted).
    """
    trainKM()
    patients = PersonExt.objects.all()
    patients_info = []
    time_prev = 24
    
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

        global_model= get_global_kaplan_model()

        global_risk = global_model.predict(time_patient)
        global_risk_prev = global_model.predict(time_patient + time_prev)

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

            model = get_kaplan_model(concept_id,measurement.value_as_number,1)
            prev = model.predict(time_patient + time_prev)
            
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
        'active_page': 'utentes'
    })

def utente(request, person_id):
    """
    @brief: View that returns the details page for a specific patient (utente), including personal data,
            clinical condition, measurement history, clinical notes, and hospitalization records.
    @param request: HTTP request (GET)
    @param person_id: Unique identifier of the patient (utente)
    @return: Renders the 'utente.html' template with the corresponding patient data
    """

    global_model= get_global_kaplan_model()

    mymember = PersonExt.objects.get(person_id=person_id)
    mycondition = ConditionOccurrence.objects.get(person_id=person_id)
    idade = mymember.idade()
    event_filter = request.GET.get('evento')

    # Agrupar medições por data e hora
    measurements = Measurement.objects.filter(person_id=person_id)
    grouped = {}
    for m in measurements:
        dt = m.measurement_datetime

        # Cálculo de tempo do utente
        visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
        tempo_utente = (dt - visita.visit_start_datetime).total_seconds() / 3600

        global_risk = global_model.predict(tempo_utente)
        if dt not in grouped:
            grouped[dt] = {
                'risk': '',  # inicializa risco
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

    servico = VisitOccurrence.objects.filter(person_id=person_id)
    notes = Note.objects.filter(person_id=person_id)

    template = loader.get_template('utente.html')
    context = {
        'mymember': mymember,
        'mycondition': mycondition,
        'idade': idade,
        'grouped_measurements': grouped,
        'notes': notes,
        'servico': servico,
        'event_filter':event_filter
    }
    return HttpResponse(template.render(context, request))


def main(request):
  template = loader.get_template('main.html')
  return HttpResponse(template.render()) 

@csrf_exempt  # Desativa a verificação CSRF para esta view
def adicionar_utente(request):

  if request.method == "POST":

      firstname = request.POST.get("firstname")
      lastname = request.POST.get("lastname")
      birthday = request.POST.get("birthday")
      if request.POST.get("gender") == "Male": gender = 1 
      else: gender = 0
      numeroUtente = request.POST.get("NumeroUtente")
      queixasEntrada = request.POST.get("QueixasEntrada")
      alergias = request.POST.get("Alergias")
      diagnosticoPrincipal = request.POST.get("DiagnosticoPrincipal")
      if request.POST.get("Serviço") == "Urgência": servico = 1 
      else: 
        if request.POST.get("Serviço") == "Internamento": servico = 2 
        else: servico = 3
      spO2 = request.POST.get("SpO2")
      necessidadeO2 = request.POST.get("NecessidadeO2")
      frequenciaCardiaca = request.POST.get("FrequenciaCardiaca")
      tASistolica = request.POST.get("TASistolica")
      tADiastolica = request.POST.get("TADiastolica")
      temperatura = request.POST.get("Temperatura")
      nívelConsciencia = request.POST.get("NívelConsciencia")
      dor = request.POST.get("Dor")

      data= date.today()
      dataHora=timezone.now()

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
          condition_start_date=data,
          condition_source_value=diagnosticoPrincipal
      )

      # Notas (Queixas e Alergias)
      if queixasEntrada:
          Note.objects.create(
              person=person,
              note_text=queixasEntrada,
              note_type_concept_id=1  
          )
      if alergias:
          Note.objects.create(
              person=person,
              note_text=alergias,
              note_type_concept_id=2  
          )

      # Medições
      if spO2:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=1,  
              value_as_number=Decimal(spO2),
              measurement_datetime=dataHora
          )
      if necessidadeO2:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=2, 
              value_as_number=int(necessidadeO2),
              measurement_datetime=dataHora
          )
      if frequenciaCardiaca:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=3,  
              value_as_number=Decimal(frequenciaCardiaca),
              measurement_datetime=dataHora
          )
       
      if tASistolica:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=4,
              value_as_number=Decimal(tASistolica),
              measurement_datetime=dataHora
          )
      if tADiastolica:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=5,  
              value_as_number=Decimal(tADiastolica),
              measurement_datetime=dataHora
          )
      if temperatura:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=6,  
              value_as_number=Decimal(temperatura),
              measurement_datetime=dataHora
            )

      if nívelConsciencia:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=7,  
              value_as_number=Decimal(nívelConsciencia),
              measurement_datetime=dataHora
          )
      if dor:
          Measurement.objects.create(
              person=person,
              measurement_concept_id=8,  
              value_as_number=int(dor),
              measurement_datetime=dataHora
          )


      VisitOccurrence.objects.create(
          person=person,
          care_site_id=int(servico) if servico else 1, 
          visit_start_datetime=dataHora
      )
    

      return redirect("/utentes/")


  
  template = loader.get_template('adicionarUtente.html')
  context = {
    'active_page': 'adicionar_utente'
}

  return HttpResponse(template.render(context))       


def editarUtente(request,person_id):
  utente = PersonExt.objects.get(person_id=person_id)
  if request.method == "POST":
      utente.first_name = request.POST.get("firstname")
      utente.last_name = request.POST.get("lastname")
      utente.birthday = request.POST.get("birthday")
      utente.gender_concept_id = request.POST.get("gender")
      utente.person_source_value = request.POST.get("NumeroUtente")
      utente.save()

      return redirect("/utentes/")
  
  return render(request, "editarUtente.html", {"utente": utente})

def nova_medicao(request, person_id):
    """
    @brief: View para inserir uma nova medição para um utente específico.
    @param request: Requisição HTTP com dados da medição
    @param person_id: ID do utente
    @return: Redireciona para a página de edição após inserção
    """
    if request.method == "POST":
        agora = datetime.now()

        Measurement.objects.create(person_id=person_id, measurement_concept_id=1, value_as_number=request.POST["spo2"], measurement_datetime=agora)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=2, value_as_number=request.POST["necessidade_o2"], measurement_datetime=agora)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=3, value_as_number=request.POST["fc"], measurement_datetime=agora)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=4, value_as_number=request.POST["ta_sistolica"], measurement_datetime=agora)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=5, value_as_number=request.POST["ta_diastolica"], measurement_datetime=agora)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=6, value_as_number=request.POST["temperatura"], measurement_datetime=agora)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=7, value_as_number=request.POST["nivel_consciencia"], measurement_datetime=agora)
        Measurement.objects.create(person_id=person_id, measurement_concept_id=8, value_as_number=request.POST["dor"], measurement_datetime=agora)

    return redirect('editarUtente', person_id=person_id)


def removerUtente(request, person_id):
    person = PersonExt.objects.get(person_id=person_id)

    if request.method == "POST":
        Measurement.objects.filter(person_id=person_id).delete()
        ConditionOccurrence.objects.filter(person_id=person_id).delete()
        Note.objects.filter(person_id=person_id).delete()
        Observation.objects.filter(person_id=person_id).delete()
        VisitOccurrence.objects.filter(person_id=person_id).delete()

        person.delete()
        return redirect("/utentes/")

    return render(request, "details.html", {"mymember": person})
  

def listarUtentes(request):
    service_filter = request.GET.get("service")
    order_by = request.GET.get("order")
    event_filter = request.GET.get("event")
    temp_prev = request.GET.get("temp_prev")
    search_query = request.GET.get('search')

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

        global_model= get_global_kaplan_model()

        global_risk = global_model.predict(tempo_utente)
        global_risk_prev = global_model.predict(tempo_utente + int(temp_prev))

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
            model = get_kaplan_model(concept_id,measurement.value_as_number,int(event_filter))
            prev = model.predict(tempo_utente + int(temp_prev))
            
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
        'active_page': 'utentes'
    })

@csrf_exempt
def importar_csv(request):
    if request.method == "POST":
        try:
            csv_file = request.FILES["csv_file"]
            df = getCSV(csv_file)

            messages.success(request, "✅ Ficheiro importado com sucesso!")
        except Exception as e:
            messages.error(request, f"❌ Erro ao importar: {e}")

        return render(request, 'main.html')

    return render(request, 'main.html')

def exportar_csv(request):
    df = trainKM()

    # Usar buffer em memória
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=detectid_export.csv'
    return response


def grafico_view(request, person_id):
    parametro = request.GET.get("parametro")  
    evento = request.GET.get("evento")
   
    if parametro == "RC":
        return grafico_global(person_id)
    
    return grafico_individual(person_id, parametro, evento)



  

