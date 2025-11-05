from django.urls import path
from .views import estatisticas_view

app_name = 'estatisticas'

urlpatterns = [
    # Adicione suas rotas aqui
    path('', estatisticas_view, name='estatisticas_view'),
]