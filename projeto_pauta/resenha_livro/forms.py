from django import forms
from .models import ResenhaLivro, Aluno, PeriodoLeitura

class ResenhaLivroForm(forms.ModelForm):
    class Meta:
        model = ResenhaLivro
        fields = ['aluno', 'nomelivro', 'nomeAutor', 'periodoLeitura', 'nomeProfessor', 'aprovada']

class AlunoForm(forms.ModelForm):
    class Meta:
        model= Aluno
        fields = ['nome', 'turma', 'matricula']

class PeriodoLeituraForm(forms.ModelForm):
    class Meta:
        model = PeriodoLeitura
        fields = ['turma', 'intervalo_leitura', 'data_resenha', 'aprovada']