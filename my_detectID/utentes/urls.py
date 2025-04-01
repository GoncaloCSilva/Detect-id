from django.urls import path
from . import views

urlpatterns = [
    path('utentes/', views.utentes, name='utentes'),
    path('utentes/details/<int:id>', views.details, name='details'),
    path('', views.main, name='main'),
    path('adicionarUtente', views.adicionarUtente, name='adicionarUtente'),
    path('utentes/editarUtente/<int:id>', views.editarUtente, name='editarUtente'),
    path("utentes/removerUtente/<int:id>/", views.removerUtente, name="removerUtente"),
]