from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Aluno, ResenhaLivro

def imprimir_resenha(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    resenhas = ResenhaLivro.objects.filter(aluno=aluno)

    return render(request, 'imprimir_resenha.html', {
        'aluno': aluno,
        'resenhas': resenhas,
    })