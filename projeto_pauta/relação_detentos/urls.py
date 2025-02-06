from django.urls import path
from .views import relacao_list, salvar_alteracoes, add_detento  # Importe a nova view

app_name = 'relação_detentos'

urlpatterns = [
    path('', relacao_list, name='relacao_list'),  # URL para a lista de detentos
    path('add/', add_detento, name='add_detento'),
    path('salvar-alteracoes/', salvar_alteracoes, name='salvar_alteracoes'),  # Nova URL para salvar alterações
]