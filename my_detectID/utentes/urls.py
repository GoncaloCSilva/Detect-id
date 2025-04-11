from django.urls import path
from . import views

urlpatterns = [
    path('utentes/', views.utentes, name='utentes'),
    path('utentes/details/<int:person_id>', views.details, name='details'),
    path('', views.main, name='main'),
    path('adicionarUtente', views.adicionarUtente, name='adicionarUtente'),
    path('utentes/editarUtente/<int:person_id>', views.editarUtente, name='editarUtente'),
    path("utentes/removerUtente/<int:person_id>/", views.removerUtente, name="removerUtente"),
    path("utentes/listarUtentes", views.listarUtentes, name="listarUtentes"),
    path('api/utentes/', views.listar_utentes_api, name='listar_utentes_api'),
    path('grafico/<int:person_id>/', views.grafico_view, name='grafico_view'),

    path('utentes2/', views.utentes2, name='utentes2'),

]