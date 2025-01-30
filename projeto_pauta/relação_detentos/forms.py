from django import forms
from .models import Relacao

class RelacaoDetentosForm(forms.ModelForm):

    
    class Meta:
        model = Relacao
        fields = '__all__'
        # widgets = {
        #     'IPEN' = forms.DateInput(attrs={'type': 'date'}),
        # }
    
    def clean(self):
        cleaned_data = super().clean()
        regime = cleaned_data.get("regime")
        pena = cleaned_data.get("pena")

        if regime in ['F', 'SA'] and not pena:
            self.add_error('pena', 'O campo "Pena" é obrigatório para os regimes "Fechado" e "Semiaberto".')

        return cleaned_data