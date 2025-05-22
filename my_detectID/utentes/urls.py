from django.urls import path
from . import views

urlpatterns = [
    path('utentes/', views.utentes, name='utentes'),
    path('utentes/utente/<int:person_id>', views.utente, name='utente'),
    path('', views.main, name='main'), 
    path('adicionar_utente', views.adicionar_utente, name='adicionar_utente'),
    path('utentes/editarUtente/<int:person_id>', views.editarUtente, name='editarUtente'),
    path('utentes/novaMedicao/<int:person_id>', views.nova_medicao, name='nova_medicao'),
    path("utentes/removerUtente/<int:person_id>/", views.removerUtente, name="removerUtente"),
    path("utentes/listarUtentes", views.listarUtentes, name="listarUtentes"),
    path('grafico/<int:person_id>/', views.grafico_view, name='grafico_view'),
    path('importar_csv/', views.importar_csv, name='importar_csv'),
    path('exportar_csv/', views.exportar_csv, name='exportar_csv'),
]