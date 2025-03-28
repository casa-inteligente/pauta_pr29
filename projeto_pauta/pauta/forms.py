from django import forms
from .models import Pauta
from bleach import clean

class PautaForm(forms.ModelForm):
    class Meta:
        model = Pauta
        fields = '__all__'
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class' : 'time-input'}),  # Alterar para o widget padrão de hora
            'intervalo_repeticao' : forms.NumberInput(attrs={'min': 1, 'placeholder': 'Dias'}),
            'numero_repeticoes' : forms.NumberInput(attrs={'min': 1, 'placeholder': 'Número de Repetições'}),
        }

    def clean_situacao(self):
        value = self.cleaned_data['situacao']
        allowed_tags = [
            'p', 'b', 'i', 'u', 'a', 'ul', 'li', 'br', 'span', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'font', 'color'
        ]  # Tags HTML permitidas
        allowed_attrs = {
            'a': ['href', 'target'],
            'span': ['style'],  # Permitir estilos inline para coloração
            'table': ['border', 'cellpadding', 'cellspacing'],  # Atributos para tabelas
            'th': ['colspan', 'rowspan'],  # Atributos para células de cabeçalho
            'td': ['colspan', 'rowspan'],  # Atributos para células de tabela
        }   
        return clean(value, tags=allowed_tags, attributes=allowed_attrs)