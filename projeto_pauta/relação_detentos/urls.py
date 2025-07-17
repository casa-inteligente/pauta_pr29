from django.urls import path
from .views import relacao_list, salvar_alteracoes, add_detento, upload_pdf, upload_regime_pdf, exctrai_date_exit_view, cadastro_trampo_view, gerar_termo_autorizacao, termo_monitorado  # Importe a nova view

app_name = 'relação_detentos'

urlpatterns = [
    path('', relacao_list, name='relacao_list'),  # URL para a lista de detentos
    path('add/', add_detento, name='add_detento'),
    path('upload_pdf/', upload_pdf, name='upload_pdf'),  # URL para upload de PDF
    path('upload_regime_pdf/', upload_regime_pdf, name='upload_regime_pdf'),  # URL para upload de PDF de regime
    path('exctrai_date_exit/', exctrai_date_exit_view, name='exctrai_date_exit'),  # URL para extrair data de saída
    path('salvar-alteracoes/', salvar_alteracoes, name='salvar_alteracoes'),  # Nova URL para salvar alterações
    path('cadastro_trampo/', cadastro_trampo_view, name='cadastro_trampo'),
    path('gerar-termo/<int:detento_id>/', gerar_termo_autorizacao, name='gerar_termo_autorizacao'),
    path('termo-monitorado/', termo_monitorado, name='termo_monitorado'),
]