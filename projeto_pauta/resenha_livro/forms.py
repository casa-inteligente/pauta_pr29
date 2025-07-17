from django import forms
from .models import ResenhaLivro, Aluno, PeriodoLeitura

class ResenhaLivroForm(forms.ModelForm):
    class Meta:
        model = ResenhaLivro
        fields = ['aluno', 'nomelivro', 'nomeAutor', 'periodoLeitura', 'nomeProfessor', 'aprovada']
        widgets = {
            'aluno': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'nomelivro': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'nomeAutor': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'periodoLeitura': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'nomeProfessor': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'aprovada': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
        }

class AlunoForm(forms.ModelForm):
    class Meta:
        model= Aluno
        fields = ['nome', 'turma', 'matricula']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'turma': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'matricula': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
        }

class PeriodoLeituraForm(forms.ModelForm):
    class Meta:
        model = PeriodoLeitura
        fields = ['turma', 'intervalo_leitura', 'data_resenha', 'aprovada']
        widgets = {
            'turma': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'intervalo_leitura': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'data_resenha': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300',
                'type': 'date'
            }),
            'aprovada': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
        }