from django.urls import path
from .views import lista_escala_servidores

app_name = 'servidores'

urlpatterns = [
    #inserção de PP

    #inserção do escala
    path('escala-servidores/', lista_escala_servidores, name='lista_escala_servidores'),
    #inserção de folga

    #inserção de férias
]