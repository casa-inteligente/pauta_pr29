from django.contrib import admin

# Register your models here.
from .models import Servidores
@admin.register(Servidores)
class ServidoresAdmin(admin.ModelAdmin):
    list_display = ['nome', 'matricula', 'setor', 'status_ativo']
    list_filter = ['setor', 'status_ativo']
    search_fields = ['nome', 'matricula', 'cpf']
    ordering = ['nome']