from django.urls import path
from .views import relacao_list

app_name = 'relação_detentos'

urlpatterns = [
    path('', relacao_list, name='relacao_list'),  # Ajuste para simplificar a URL
]
