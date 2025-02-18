from django.shortcuts import render, get_object_or_404
from .models import Aluno, ResenhaLivro

def listar_alunos(request):
    alunos = Aluno.objects.all()
    return render(request, 'listar_alunos.html', {'alunos': alunos})

def imprimir_resenha(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    resenhas = ResenhaLivro.objects.filter(aluno=aluno)
    linhas = range(30)
    return render(request, 'imprimir_resenha.html', {
        'aluno': aluno,
        'resenhas': resenhas,
        'linhas': linhas,
    })