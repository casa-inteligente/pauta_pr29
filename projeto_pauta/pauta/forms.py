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
        allowed_tags = ['p', 'b', 'i', 'u', 'a', 'ul', 'li', 'br']  # Tags HTML permitidas
        allowed_attrs = {'a': ['href', 'target']}  # Atributos permitidos
        return clean(value, tags=allowed_tags, attributes=allowed_attrs)