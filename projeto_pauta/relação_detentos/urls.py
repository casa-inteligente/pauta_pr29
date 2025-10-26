from django.urls import path
from .views import relacao_list, salvar_alteracoes, upload_pdf, upload_regime_pdf, exctrai_date_exit_view, cadastro_trampo_view, gerar_termo_autorizacao, termo_monitorado, gerar_termo_kit_higiene, view_termo_rouparia, gerar_termo_rouparia

app_name = 'relação_detentos'

urlpatterns = [
    path('', relacao_list, name='relacao_list'),  # URL para a lista de detentos
    
    path('upload_pdf/', upload_pdf, name='upload_pdf'),  # URL para upload de PDF
    path('upload_regime_pdf/', upload_regime_pdf, name='upload_regime_pdf'),  # URL para upload de PDF de regime
    path('exctrai_date_exit/', exctrai_date_exit_view, name='exctrai_date_exit'),  # URL para extrair data de saída
    path('salvar-alteracoes/', salvar_alteracoes, name='salvar_alteracoes'),  # Nova URL para salvar alterações
    path('cadastro_trampo/', cadastro_trampo_view, name='cadastro_trampo'),
    path('gerar-termo/<int:detento_id>/<str:empresa_conveniada>/', gerar_termo_autorizacao, name='gerar_termo_autorizacao'),
    path('termo-monitorado/<int:detento_ipen>/', termo_monitorado, name='termo_monitorado'),
    path('termo-kit-higiene/', gerar_termo_kit_higiene, name='gerar_termo_kit_higiene'),
    path('termo-rouparia/', view_termo_rouparia, name='view_termo_rouparia'),
    path('gerar-termo-rouparia/<int:detento_id>/<int:numero_kit>/<str:regime>/', gerar_termo_rouparia, name='gerar_termo_rouparia'),
]