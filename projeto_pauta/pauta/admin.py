from django.contrib import admin
from .models import  Pauta
from .forms import PautaForm
from django.conf.locale.pt_BR import formats as pt_BR_formats
from django.utils import timezone
from datetime import timedelta
# Register your models here.

#define formato 24H
pt_BR_formats.TIME_FORMAT = 'H:i'
pt_BR_formats.DATETIME_FORMAT = 'd/m/Y H:i'

@admin.register(Pauta)
class PautaAdmin(admin.ModelAdmin):
    form = PautaForm
    list_display = ('data_formatada', 'hora_formatada', 'nome', 'situacao')
    search_fields = ('nome', 'data')
    list_filter = ('data', 'nome')
    ordering = ('data', 'hora')
    change_form_template = 'admin/pauta/change_form.html'  # Especifica o template personalizado

    #Cria condição para repetição
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.intervalo_repeticao and obj.numero_repeticoes:
            data_atual = obj.data

            #inicia no 2 pois o primeiro já foi adicionado
            for i in range(2, obj.numero_repeticoes + 1):
                nova_data = data_atual + timedelta(days=obj.intervalo_repeticao)
                Pauta.objects.create(
                    data = nova_data,
                    hora = obj.hora,
                    nome = obj.nome,
                    situacao = obj.situacao,
                    intervalo_repeticao = None,
                    numero_repeticoes = None
                )
                data_atual = nova_data #Atualiza data para interação

    #Formata a data exibida no admin
    def data_formatada(self, obj):
        return obj.data.strftime('%d/%m/%Y')
    data_formatada.admin_order_field = 'data'
    data_formatada.short_description = 'Data'
    #Formata a exibição da hora
    def hora_formatada(self, obj):
        return obj.hora.strftime('%H:%M')
    hora_formatada.admin_order_field = 'hora'
    hora_formatada.short_description = 'Hora'