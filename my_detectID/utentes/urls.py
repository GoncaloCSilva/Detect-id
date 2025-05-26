from django.urls import path
from . import views

urlpatterns = [
    path('utentes/', views.patients, name='patients'),
    path('utentes/utente/<int:person_id>', views.patient, name='patient'),
    path('', views.main, name='main'), 
    path('adicionar_utente', views.addPatient, name='addPatient'),
    path('utentes/editarUtente/<int:person_id>', views.editPatient, name='editPatient'),
    path('utentes/novaMedicao/<int:person_id>', views.newMeasurement, name='newMeasurement'),
    path("utentes/removerUtente/<int:person_id>/", views.removePatient, name="removePatient"),
    path("utentes/listarUtentes", views.listPatients, name="listPatients"),
    path('grafico/<int:person_id>/', views.graphicView, name='graphic_view'),
    path('importar_csv/', views.importCSV, name='importCSV'),
    path('exportar_csv/', views.exportCSV, name='exportCSV'),
]