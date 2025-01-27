from dateutil.relativedelta import relativedelta
from django.contrib import admin
from .models import Pauta
from .forms import PautaForm
from django.conf.locale.pt_BR import formats as pt_BR_formats
from django.utils import timezone
from datetime import timedelta

# Register your models here.

# Define formato 24H
pt_BR_formats.TIME_FORMAT = 'H:i'
pt_BR_formats.DATETIME_FORMAT = 'd/m/Y H:i'


# Cria filtro personalizado para selecionar ano anterior
class AnoAnteriorFilter(admin.SimpleListFilter):
    ano_atual = timezone.now().year
    ano_anterior = ano_atual - 1
    title = f'Ano de: {ano_anterior}'
    parameter_name = 'ano_anterior'

    def lookups(self, request, model_admin):
        return (
            ('ano_anterior', 'Ano Anterior'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'ano_anterior':
            ano_atual = timezone.now().year
            ano_anterior = ano_atual - 1
            inicio_ano_anterior = timezone.datetime(ano_anterior, 1, 1)
            fim_ano_anterior = timezone.datetime(ano_anterior, 12, 31, 23, 59, 59)
            return queryset.filter(data__range=(inicio_ano_anterior, fim_ano_anterior))
        return queryset


@admin.register(Pauta)
class PautaAdmin(admin.ModelAdmin):
    form = PautaForm
    list_display = ('data_formatada', 'hora_formatada', 'nome', 'situacao')
    search_fields = ('nome', 'data', 'situacao')
    list_filter = ('data', AnoAnteriorFilter, 'nome')
    ordering = ('data', 'hora')
    change_form_template = 'admin/pauta/change_form.html'  # Especifica o template personalizado

    # Cria condição para repetição
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.intervalo_repeticao and obj.numero_repeticoes:
            data_atual = obj.data
            #print(obj.intervalo_repeticao)

            for i in range(1, obj.numero_repeticoes):
                if obj.intervalo_repeticao == 30:
                    data_atual += relativedelta(months=1)
                elif obj.intervalo_repeticao == 15:
                    data_atual += relativedelta(weeks=2)
                elif obj.intervalo_repeticao == 21:
                    data_atual += relativedelta(weeks=3)
                else:
                    data_atual += relativedelta(days=obj.intervalo_repeticao)
                
                Pauta.objects.create(
                    data=data_atual,
                    hora=obj.hora,
                    nome=obj.nome,
                    situacao=obj.situacao,
                    intervalo_repeticao=None,
                    numero_repeticoes=None
                )

    # Formata a data exibida no admin
    def data_formatada(self, obj):
        return obj.data.strftime('%d/%m/%Y')
    data_formatada.admin_order_field = 'data'
    data_formatada.short_description = 'Data'

    # Formata a exibição da hora
    def hora_formatada(self, obj):
        return obj.hora.strftime('%H:%M')
    hora_formatada.admin_order_field = 'hora'
    hora_formatada.short_description = 'Hora'
