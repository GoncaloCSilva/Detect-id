from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Utente
from django.template import loader


# Create your views here.
def utentes(request):
  mymembers = Utente.objects.all().values()
  template = loader.get_template('utentes.html')
  context = {
    'mymembers': mymembers,
  }
  return HttpResponse(template.render(context, request))

def details(request, id):
  mymember = Utente.objects.get(id=id)
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



