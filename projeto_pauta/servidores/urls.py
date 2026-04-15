from django.urls import path
from .views import (
    lista_escala_servidores, 
    escala_proximo_mes, 
    escala_historico, 
    folha_ponto,
    todas_folhas_ponto,
    folha_ponto_servidor, 
    frase_motivacional,
    gerador_oficios,
)

app_name = 'servidores'

urlpatterns = [
    #inserção de PP

    # Escala do mês atual
    path('escala-servidores/', lista_escala_servidores, name='lista_escala_servidores'),
    
    # Escala do próximo mês
    path('escala-proximo-mes/', escala_proximo_mes, name='escala_proximo_mes'),
    
    # Histórico de escalas
    path('escala-historico/', escala_historico, name='escala_historico'),
    #inserção de folga

    #inserção de férias

    # Folha Ponto
    path('folha-ponto/', folha_ponto, name='folha_ponto'),
    path('folha-ponto/pdf/<int:mes>/<int:ano>/', todas_folhas_ponto, name='folha_ponto_pdf'),
    path('folha-ponto/servidor/<int:servidor_id>/<int:mes>/<int:ano>/', folha_ponto_servidor, name='folha_ponto_servidor'),

    
    path('frase-motivacional/', frase_motivacional, name='frase_motivacional'),
    path('gerador-oficios/', gerador_oficios, name='gerador_oficios'),
]