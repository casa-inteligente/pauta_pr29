from django.urls import path
from .views import listar_alunos, imprimir_resenha

app_name = 'resenha_livro'

urlpatterns = [
    path('', listar_alunos, name='listar_alunos'),
    path('imprimir_resenha/<int:aluno_id>/', imprimir_resenha, name='imprimir_resenha'),
    # Outras URLs...
]