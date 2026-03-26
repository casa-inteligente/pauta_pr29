# pauta_pr29/projeto_pauta/resenha_livro/urls.py

from django.urls import path
from .views import (
    listar_alunos, imprimir_resenha,
    adicionar_resenha, editar_resenha,
    gerar_todas_resenhas,  adicionar_aluno_popup,
    excluir_resenha, configuracao_resenhas,
    adicionar_periodo_leitura, alternar_gerado_declaracao, gerar_declaracao,
    popup_confirmar_geracao_declaracao, gerar_declaracoes_selecionadas
)

app_name = 'resenha_livro'

urlpatterns = [
    path('', listar_alunos, name='listar_alunos'),
    path('imprimir_resenha/<int:aluno_id>/<int:periodo_id>/', imprimir_resenha, name='imprimir_resenha'),
    path('adicionar_resenha/', adicionar_resenha, name='adicionar_resenha'),
    path('editar_resenha/<int:resenha_id>/', editar_resenha, name='editar_resenha'),
    path('gerar_todas_resenhas/<int:periodo_id>/', gerar_todas_resenhas, name='gerar_todas_resenhas'),
    path('adicionar_aluno_popup/', adicionar_aluno_popup, name='adicionar_aluno_popup'),
    path('excluir_resenha/<int:resenha_id>/', excluir_resenha, name='excluir_resenha'),
    path('configuracao_resenhas/', configuracao_resenhas, name='configuracao_resenhas'),
    path('adicionar_periodo_leitura/', adicionar_periodo_leitura, name='adicionar_periodo_leitura'),

    # Declaração
    path('gerar_declaracao/', gerar_declaracao, name='gerar_declaracao'),
    path('alternar_gerado_declaracao/<int:resenha_id>/', alternar_gerado_declaracao, name='alternar_gerado_declaracao'),
    path('popup_confirmar_geracao_declaracao/', popup_confirmar_geracao_declaracao, name='popup_confirmar_geracao_declaracao'),
    path('gerar_declaracoes_selecionadas/', gerar_declaracoes_selecionadas, name='gerar_declaracoes_selecionadas'),
]