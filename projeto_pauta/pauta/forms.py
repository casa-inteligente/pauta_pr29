from django import forms
from .models import Pauta
import bleach

class PautaForm(forms.ModelForm):
    class Meta:
        model = Pauta
        fields = '__all__'
        widgets = {
            'data': forms.DateInput(attrs={
                'type': 'date',
                'class': 'date-input w-50 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
                }),
            'hora': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-70 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-pink-300',
                'placeholder': 'Hora'
                }),
            'nome': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-red-300',
                'placeholder': 'Nome'
            }),
            'intervalo_repeticao' : forms.NumberInput(attrs={
                'min': 1,
                'max': 365, 
                'placeholder': 'Dias (Não implementado)',
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
            'numero_repeticoes' : forms.NumberInput(attrs={
                'min': 2, 
                'max': 50,
                'placeholder': 'Número de Repetições',
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300'
            }),
        }

    def clean_situacao(self):
        """Sanitiza o HTML do campo situacao"""
        value = self.cleaned_data.get('situacao', '')
        
        if not value:
            return value
        
        # Configuração simplificada do bleach
        ALLOWED_TAGS = [
            'p', 'b', 'i', 'u', 'a', 'ul', 'ol', 'li', 'br', 'span', 
            'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'div', 'blockquote', 'code', 'pre', 'hr'
        ]
        
        ALLOWED_ATTRIBUTES = {
            'a': ['href', 'title', 'target'],
            'span': ['style'],
            'p': ['style'],
            'div': ['class'],
            'table': ['class'],
            'th': ['colspan', 'rowspan'],
            'td': ['colspan', 'rowspan'],
        }
        
        # Limpar HTML
        try:
            cleaned = bleach.clean(
                value,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
            return cleaned
        except Exception as e:
            # Se der erro, retorna o valor sem limpar
            print(f"Erro ao limpar HTML: {e}")
            return value