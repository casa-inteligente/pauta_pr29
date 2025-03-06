from django.shortcuts import render, get_object_or_404
from .models import Aluno, ResenhaLivro

def listar_alunos(request):
    alunos = Aluno.objects.using('resenha_livro').all()
    return render(request, 'listar_alunos.html', {'alunos': alunos})

def imprimir_resenha(request, aluno_id):
    aluno = get_object_or_404(Aluno.objects.using('resenha_livro'), id=aluno_id)
    resenhas = ResenhaLivro.objects.using('resenha_livro').filter(aluno=aluno)
    
    linhas_por_pagina = 69  # Altura disponível dividido pelo espaçamento (297mm - margens e header)
    linhas = range(linhas_por_pagina)
    
    return render(request, 'imprimir_resenha.html', {
        'aluno': aluno,
        'resenhas': resenhas,
        'linhas': linhas,
    })