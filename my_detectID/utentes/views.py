from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.template import loader
from rest_framework.response import Response
from rest_framework.decorators import api_view
import matplotlib.pyplot as plt
from io import BytesIO
from .graficos import grafico
from datetime import date
from collections import defaultdict
from .bd import *


# Create your views here.
def utentes(request):
  mymembers = Person.objects.all().values()
  template = loader.get_template('utentes.html')
  context = {
    'mymembers': mymembers,
    'active_page': 'utentes'
  }
  return HttpResponse(template.render(context, request))

def details(request, person_id):
    #Utente
    mymember = Person.objects.get(person_id=person_id)
    # Diagnóstico
    mycondition = ConditionOccurrence.objects.get(person_id=person_id)
    idade = mymember.idade()

    # Medições
    measurements = Measurement.objects.filter(person_id=person_id)
    grouped = {}
    for m in measurements:
        dt = m.measurement_datetime
        if dt not in grouped:
            grouped[dt] = []
        grouped[dt].append(m)

    #Serviço
    servico = VisitOccurrence.objects.filter(person_id=person_id)
    
    #Alergias e Queixas
    notes = Note.objects.filter(person_id=person_id)
    template = loader.get_template('details.html')
    context = {
        'mymember': mymember,
        'mycondition': mycondition,
        'idade': idade,
        'grouped_measurements': grouped,
        'notes':notes,
        'servico':servico
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
      gender = request.POST.get("gender")
      numeroUtente = request.POST.get("NumeroUtente")
      queixasEntrada = request.POST.get("QueixasEntrada")
      alergias = request.POST.get("Alergias")
      diagnosticoPrincipal = request.POST.get("DiagnosticoPrincipal")
      servico = request.POST.get("Serviço")
      spO2 = request.POST.get("SpO2")
      necessidadeO2 = request.POST.get("NecessidadeO2")
      frequenciaCardiaca = request.POST.get("FrequenciaCardiaca")
      tASistolica = request.POST.get("TASistolica")
      tADiastolica = request.POST.get("TADiastolica")
      temperatura = request.POST.get("Temperatura")
      nívelConsciencia = request.POST.get("NívelConsciencia")
      dor = request.POST.get("Dor")


      return redirect("/utentes/")

  
  template = loader.get_template('adicionarUtente.html')
  context = {
    'active_page': 'adicionar_utente'
}

  return HttpResponse(template.render(context))       


def editarUtente(request,id):
  # utente = Utente.objects.get(id=id)
  # if request.method == "POST":
  #     utente.firstname = request.POST.get("firstname")
  #     utente.lastname = request.POST.get("lastname")
  #     utente.birthday = request.POST.get("birthday")
  #     utente.gender = request.POST.get("gender")
  #     utente.risk = request.POST.get("risk")
  #     utente.save()

  #     return redirect("/utentes/")
  
  return render(request, "editarUtente.html", {"utente": utente})


def removerUtente(request,id):
  # utente = Utente.objects.get(id=id)
  # if request.method == "POST":
  #       utente.delete()
  #       return redirect("/utentes/")

  return render(request,"details.html",{"mymember":utente})
  

def listarUtentes(request):
    risk_filter = request.GET.get("risk")  
    order_by = request.GET.get("order") 

    utentes = Person.objects.all()
    # if risk_filter in ["High Risk", "Some Risk", "No Risk"]:
    #     utentes = utentes.filter(risk=risk_filter)

    if order_by in ["first_name", "-first_name", "last_name", "-last_name", "birthday", "-birthday"]:
        utentes = utentes.order_by(order_by)

    return render(request, "utentes.html", {"mymembers": utentes, "risk_filter": risk_filter, "order_by": order_by})

def grafico_view(request, person_id):

    grafico()

    # Salvar o gráfico em memória
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')


  

