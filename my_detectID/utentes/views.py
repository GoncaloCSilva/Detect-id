from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Person
from .models import Utente
from django.template import loader
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import UtenteSerializer
import matplotlib.pyplot as plt
from io import BytesIO
from .graficos import grafico
from .bd import *


# Create your views here.
def utentes(request):
  mymembers = Person.objects.all().values()
  template = loader.get_template('utentes.html')
  context = {
    'mymembers': mymembers,
  }
  return HttpResponse(template.render(context, request))

def utentes2(request):
  mymembers = Utente.objects.all().values()
  template = loader.get_template('utentes2.html')
  fetchUtentes = getUtentes()

  context = {
    'mymembers': fetchUtentes,
  }
  return HttpResponse(template.render(context, request))

def details(request, person_id):
  mymember = Person.objects.get(person_id=person_id)
  template = loader.get_template('details.html')
  context = {
    'mymember': mymember,
  }
  return HttpResponse(template.render(context, request))


def main(request):
  template = loader.get_template('main.html')
  return HttpResponse(template.render()) 

@csrf_exempt  # Desativa a verificação CSRF para esta view
def adicionarUtente(request):

  if request.method == "POST":

      firstname = request.POST.get("firstname")
      lastname = request.POST.get("lastname")
      birthday = request.POST.get("birthday")
      gender = request.POST.get("gender")
      risk = request.POST.get("risk")

      Utente.objects.create(
          firstname=firstname, lastname=lastname, birthday=birthday, gender=gender, risk=risk
      )

      return redirect("/utentes/")

  
  template = loader.get_template('adicionarUtente.html')
  return HttpResponse(template.render())       


def editarUtente(request,id):
  utente = Utente.objects.get(id=id)
  if request.method == "POST":
      utente.firstname = request.POST.get("firstname")
      utente.lastname = request.POST.get("lastname")
      utente.birthday = request.POST.get("birthday")
      utente.gender = request.POST.get("gender")
      utente.risk = request.POST.get("risk")
      utente.save()

      return redirect("/utentes/")
  
  return render(request, "editarUtente.html", {"utente": utente})


def removerUtente(request,id):
  utente = Utente.objects.get(id=id)
  if request.method == "POST":
        utente.delete()
        return redirect("/utentes/")

  return render(request,"details.html",{"mymember":utente})
  

def listarUtentes(request):
    risk_filter = request.GET.get("risk", "")  
    order_by = request.GET.get("order", "firstname") 

    utentes = Utente.objects.all()
    if risk_filter in ["High Risk", "Some Risk", "No Risk"]:
        utentes = utentes.filter(risk=risk_filter)

    if order_by in ["firstname", "-firstname", "lastname", "-lastname", "birthday", "-birthday"]:
        utentes = utentes.order_by(order_by)

    return render(request, "utentes.html", {"mymembers": utentes, "risk_filter": risk_filter, "order_by": order_by})

def grafico_view(request, person_id):

    grafico()

    # Salvar o gráfico em memória
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')


@api_view(['GET'])
def listar_utentes_api(request):
    utentes = Utente.objects.all()
    serializer = UtenteSerializer(utentes, many=True)
    return Response(serializer.data)
  

