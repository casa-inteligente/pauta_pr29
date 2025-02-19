from django.urls import path
from .views import relacao_list, salvar_alteracoes, add_detento, upload_pdf, upload_regime_pdf, exctrai_date_exit_view  # Importe a nova view

app_name = 'relação_detentos'

urlpatterns = [
    path('', relacao_list, name='relacao_list'),  # URL para a lista de detentos
    path('add/', add_detento, name='add_detento'),
    path('upload_pdf/', upload_pdf, name='upload_pdf'),
    path('upload_regime_pdf/', upload_regime_pdf, name='upload_regime_pdf'),
    path('exctrai_date_exit/', exctrai_date_exit_view, name='exctrai_date_exit'),
    path('salvar-alteracoes/', salvar_alteracoes, name='salvar_alteracoes'),  # Nova URL para salvar alterações
]