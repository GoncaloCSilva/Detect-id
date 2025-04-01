from django.urls import path
from . import views

urlpatterns = [
    path('utentes/', views.utentes, name='utentes'),
    path('utentes/details/<int:id>', views.details, name='details'),
    path('', views.main, name='main'),
    path('adicionarUtente', views.adicionarUtente, name='adicionarUtente'),
    
]