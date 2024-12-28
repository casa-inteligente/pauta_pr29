from django import forms
from .models import Pauta

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