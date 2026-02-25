from django.contrib import admin
from .models import Relacao, DescricaoKitHigiene, Descricao_termo_rouparia, CalculoAlimentacao
# Remover o import problemático ou criar o form se necessário
# from .forms import RelacaoDetentosForm

# Register your models here.
@admin.register(Relacao)
class RelacaoAdmin(admin.ModelAdmin):
    list_display = ['IPEN', 'nome', 'regime', 'local_alocacao']
    list_filter = ['regime', 'local_alocacao']
    search_fields = ['IPEN', 'nome']
    ordering = ['nome']

@admin.register(DescricaoKitHigiene)
class DescricaoKitHigieneAdmin(admin.ModelAdmin):
    list_display = ['id']
    
@admin.register(Descricao_termo_rouparia)
class DescricaoTermoRoupariaAdmin(admin.ModelAdmin):
    list_display = ['id']

@admin.register(CalculoAlimentacao)
class CalculoAlimentacaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'atualizado_em']