# compromissos/admin.py
from django.contrib import admin
from .models import Compromisso
from django.forms import ModelForm, DateInput, TimeInput

class CompromissoForm(ModelForm):
    class Meta:
        model = Compromisso
        fields = '__all__'
        widgets = {
            'data': DateInput(attrs={'type': 'date'}),
            'horario': TimeInput(attrs={'type': 'time'})  # Alterar para o widget padrão de hora
        }

class CompromissoAdmin(admin.ModelAdmin):
    form = CompromissoForm

admin.site.register(Compromisso, CompromissoAdmin)
