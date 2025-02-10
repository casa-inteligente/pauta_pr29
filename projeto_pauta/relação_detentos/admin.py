from django.contrib import admin
from .models import Relacao
from .forms import RelacaoDetentosForm

# Register your models here.
@admin.register(Relacao)
class RelacaoAdmin(admin.ModelAdmin):
    form = RelacaoDetentosForm
    list_display = ('IPEN', 'nome', 'comarca', 'artigo', 'formatted_ingresso', 'regime', 'pena', 'formatted_previsao_saida', 'local_alocacao', 'observacoes', 'formatted_atualizado')
    search_fields = ('nome', "ingresso", 'formatted_previsao_saida')

# @admin.register(Pena)
# class PenaAdmin(admin.ModelAdmin):
#     list_display = ('ano', 'mes', 'dias')
#@admin.display()