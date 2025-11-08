from django.contrib import admin

# Register your models here.
from .models import Servidores, ServidorFerias, ServidorAtestadoMedico, ServidorFolgaCompensatoria

@admin.register(Servidores)
class ServidoresAdmin(admin.ModelAdmin):
    list_display = ['nome', 'matricula', 'setor', 'status_ativo']
    list_filter = ['setor', 'status_ativo']
    search_fields = ['nome', 'matricula', 'cpf']
    ordering = ['nome']

@admin.register(ServidorFerias)
class ServidorFeriasAdmin(admin.ModelAdmin):
    list_display = ['servidor', 'inicio_ferias', 'fim_ferias']
    list_filter = ['servidor']
    search_fields = ['servidor__nome']
    ordering = ['servidor']

@admin.register(ServidorAtestadoMedico)
class ServidorAtestadoMedicoAdmin(admin.ModelAdmin):
    list_display = ['servidor', 'data_inicio', 'data_fim']
    list_filter = ['servidor']
    search_fields = ['servidor__nome']
    ordering = ['servidor']

@admin.register(ServidorFolgaCompensatoria)
class ServidorFolgaCompensatoriaAdmin(admin.ModelAdmin):
    list_display = ['servidor', 'data_folga']
    list_filter = ['servidor']
    search_fields = ['servidor__nome']
    ordering = ['servidor']