from django import forms
from .models import Relacao

class RelacaoDetentosForm(forms.ModelForm):
    class Meta:
        model = Relacao
        fields = '__all__'
        widgets = {
            'IPEN' = forms.DateInput(attrs={'type': 'date'}),
        }