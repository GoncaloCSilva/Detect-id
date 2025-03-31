from django.shortcuts import render
from django.http import HttpResponse
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



