from django.urls import path
from . import views

app_name = 'resenha_livro'

urlpatterns = [
    path('imprimir_resenha/<int:aluno_id>/', views.imprimir_resenha, name='imprimir_resenha'),
    # Outras URLs...
]