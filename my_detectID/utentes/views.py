from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.template import loader
from rest_framework.decorators import api_view
import matplotlib.pyplot as plt
from io import BytesIO
from .hd_graficos import grafico, grafico_individual
from datetime import date, datetime
from decimal import Decimal
from django.utils import timezone
from .models import PersonExt, Measurement
from django.shortcuts import render



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
    @brief: Página que lista todos os utentes com a última medição clínica.
    """
    utentes = PersonExt.objects.all()
    utentes_info = []
    # Para cada utente vai buscar a última medição feita de cada parametro e guarda o seu valor,
    # Tudo é juntado em utentes_info para ser mais facil mostrar na pagina Utentes
    for utente in utentes:
        last_measurements = {}
        for key, concept_id in CONCEPT_IDS.items():
            measurement = (
                Measurement.objects
                .filter(person_id=utente.person_id, measurement_concept_id=concept_id)
                .order_by('-measurement_datetime')
                .first()
            )
            last_measurements[key] = measurement.value_as_number if measurement else None

        utentes_info.append({
            'person': utente,
            **last_measurements
        })
    
    return render(request, 'utentes.html', {
        'mymembers': utentes_info,
        'active_page': 'utentes'
    })

def details(request, person_id):
    """
    @brief: Função que retorna a página de detalhes de um utente, incluindo os dados pessoais, condição,
            histórico de medições, notas e serviço de internamento.
    @param request: Requisição HTTP
    @param person_id: ID do utente
    @return: Renderiza o template 'details.html' com os dados do utente
    """
    mymember = PersonExt.objects.get(person_id=person_id)
    mycondition = ConditionOccurrence.objects.get(person_id=person_id)
    idade = mymember.idade()

    # Agrupar medições por data e hora
    measurements = Measurement.objects.filter(person_id=person_id)
    grouped = {}
    for m in measurements:
        dt = m.measurement_datetime
        if dt not in grouped:
            grouped[dt] = []
        grouped[dt].append(m)

    grouped = dict(sorted(grouped.items(), key=lambda item: item[0], reverse=True))

    servico = VisitOccurrence.objects.filter(person_id=person_id)
    notes = Note.objects.filter(person_id=person_id)

    template = loader.get_template('details.html')
    context = {
        'mymember': mymember,
        'mycondition': mycondition,
        'idade': idade,
        'grouped_measurements': grouped,
        'notes': notes,
        'servico': servico
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

    CARE_SITE_MAP = {
        1: "Urgência",
        2: "Internamento",
        3: "UCI",
    }

    utentes = PersonExt.objects.all()

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

    # Fetch latest measurements just like in `utentes`
    utentes_info = []
    for utente in utentes:
        last_measurements = {}
        for key, concept_id in CONCEPT_IDS.items():
            measurement = (
                Measurement.objects
                .filter(person_id=utente.person_id, measurement_concept_id=concept_id)
                .order_by('-measurement_datetime')
                .first()
            )
            last_measurements[key] = measurement.value_as_number if measurement else None

        utentes_info.append({
            'person': utente,
            **last_measurements
        })

    return render(request, "utentes.html", {
        "mymembers": utentes_info,
        "service_filter": service_filter,
        "order_by": order_by
    })


# def listarUtentes(request):
#     service_filter = request.GET.get("service")
#     order_by = request.GET.get("order")

#     CARE_SITE_MAP = {
#         1: "Urgência",
#         2: "Internamento",
#         3: "UCI",
#     }

#     utentes = PersonExt.objects.all()

#     if service_filter in CARE_SITE_MAP.values():
#         service_id = [k for k, v in CARE_SITE_MAP.items() if v == service_filter][0]

#         person_ids = VisitOccurrence.objects.filter(
#             care_site_id=service_id
#         ).values_list("person_id", flat=True).distinct()

#         utentes = utentes.filter(person_id__in=person_ids)

#     if order_by in ["first_name", "-first_name", "last_name", "-last_name", "birthday", "-birthday"]:
#         utentes = utentes.order_by(order_by)

#     return render(request, "utentes.html", {
#         "mymembers": utentes,
#         "service_filter": service_filter,
#         "order_by": order_by
#     })



def grafico_view(request, person_id):
    return grafico_individual(person_id)



  

