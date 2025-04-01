from django import forms
from .models import ResenhaLivro, Aluno

class ResenhaLivroForm(forms.ModelForm):
    class Meta:
        model = ResenhaLivro
        fields = ['aluno', 'nomelivro', 'nomeAutor', 'periodoLeitura', 'nomeProfessor']

class AlunoForm(forms.ModelForm):
    class Meta:
        model= Aluno
        fields = ['nome', 'turma']