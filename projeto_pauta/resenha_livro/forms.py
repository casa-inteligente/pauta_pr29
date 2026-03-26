from django import forms
from .models import ResenhaLivro, Aluno, PeriodoLeitura
from relação_detentos.forms.django_toggle_switch import ToggleSwitchWidget

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
            'aprovada': ToggleSwitchWidget(
                size='md',
                active_color='#16a34a',
                inactive_color='#cbd5e1',
                active_text='Aprovado',
                inactive_text='Reprovado',
                show_label=True,
            ),
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
            'aprovada': ToggleSwitchWidget(
                size='md',
                active_color='#16a34a',
                inactive_color='#cbd5e1',
                active_text='Aprovado',
                inactive_text='Reprovado',
                show_label=True,
            ),
        }