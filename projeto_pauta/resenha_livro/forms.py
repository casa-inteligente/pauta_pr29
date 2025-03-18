from django import forms
from .models import ResenhaLivro

class ResenhaLivroForm(forms.ModelForm):
    class Meta:
        model = ResenhaLivro
        fields = ['aluno', 'nomelivro', 'nomeAutor', 'periodoLeitura', 'nomeProfessor']