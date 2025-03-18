from django.urls import path
from .views import listar_alunos, imprimir_resenha, adicionar_resenha, editar_resenha, gerar_todas_resenhas

app_name = 'resenha_livro'

urlpatterns = [
    path('', listar_alunos, name='listar_alunos'),
    path('imprimir_resenha/<int:aluno_id>/', imprimir_resenha, name='imprimir_resenha'),
    path('adicionar_resenha/', adicionar_resenha, name='adicionar_resenha'),
    path('editar_resenha/<int:resenha_id>/', editar_resenha, name='editar_resenha'),
    path('gerar_todas_resenhas/<int:periodo_id>/', gerar_todas_resenhas, name='gerar_todas_resenhas'),
    # Outras URLs...
]