from django.urls import path
from . import views

urlpatterns = [
    path('utentes/', views.utentes, name='utentes'),
    path('utentes/details/<int:person_id>', views.details, name='details'),
    path('', views.main, name='main'),
    path('adicionar_utente', views.adicionar_utente, name='adicionar_utente'),
    path('utentes/editarUtente/<int:person_id>', views.editarUtente, name='editarUtente'),
    path("utentes/removerUtente/<int:person_id>/", views.removerUtente, name="removerUtente"),
    path("utentes/listarUtentes", views.listarUtentes, name="listarUtentes"),
    path('grafico/<int:person_id>/', views.grafico_view, name='grafico_view'),
]