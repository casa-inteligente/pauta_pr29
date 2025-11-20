from django.urls import path
from .views import lista_escala_servidores, escala_proximo_mes, escala_historico

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
]