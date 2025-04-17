from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.template import loader
from rest_framework.response import Response
from rest_framework.decorators import api_view
import matplotlib.pyplot as plt
from io import BytesIO
from .hd_graficos import grafico
from datetime import date, datetime
from collections import defaultdict
from decimal import Decimal
from django.utils import timezone



# Create your views here.
def utentes(request):
  """
  @brief: Função que retorna a lista de utentes
  @param request: Requisição HTTP
    @return: Renderiza o template 'utentes.html' com a lista de utentes
  """
  mymembers = PersonExt.objects.all().values()
  template = loader.get_template('utentes.html')
  context = {
    'mymembers': mymembers,
    'active_page': 'utentes'
  }
  return HttpResponse(template.render(context, request))

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

    # Ordenar o dicionário do mais recente para o mais antigo
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
    
      # firstname = request.POST.get("firstname")
      # lastname = request.POST.get("lastname")
      # birthday = request.POST.get("birthday")
      # gender = request.POST.get("gender")
      # risk = request.POST.get("risk")

      # Utente.objects.create(
      #     firstname=firstname, lastname=lastname, birthday=birthday, gender=gender, risk=risk
      # )

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
    risk_filter = request.GET.get("risk")  
    order_by = request.GET.get("order") 

    utentes = PersonExt.objects.all()
    # if risk_filter in ["High Risk", "Some Risk", "No Risk"]:
    #     utentes = utentes.filter(risk=risk_filter)

    if order_by in ["first_name", "-first_name", "last_name", "-last_name", "birthday", "-birthday"]:
        utentes = utentes.order_by(order_by)

    return render(request, "utentes.html", {"mymembers": utentes, "risk_filter": risk_filter, "order_by": order_by})

def grafico_view(request, person_id):

    grafico()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')


  

