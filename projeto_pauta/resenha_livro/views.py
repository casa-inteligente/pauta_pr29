import os
from django.templatetags.static import static
from django.shortcuts import render, get_object_or_404
from .models import Aluno, ResenhaLivro
from django.conf import settings

def listar_alunos(request):
    alunos = Aluno.objects.using('resenha_livro').all()
    # static_path = static('resenha_livro/css/listar_alunos.css')
    # static_path = static('resenha_livro/css/listar_alunos.css')
    # full_static_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'resenha_livro', 'css', 'listar_alunos.css')
    # print(f'O caminho da folha é:\t{full_static_path}')
    return render(request, 'listar_alunos.html', {'alunos': alunos})

def imprimir_resenha(request, aluno_id):
    aluno = get_object_or_404(Aluno.objects.using('resenha_livro'), id=aluno_id)
    resenhas = ResenhaLivro.objects.using('resenha_livro').filter(aluno=aluno)
    linhas = range(50)
    
    return render(request, 'imprimir_resenha.html', {
        'aluno': aluno,
        'resenhas': resenhas,
        'linhas': linhas,
    })


def adicionar_resenha():
    pass