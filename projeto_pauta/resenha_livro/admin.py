from django.contrib import admin
from .models import ResenhaLivro, PeriodoLeitura



@admin.register(ResenhaLivro) # Para exibir no admin
class Resenha(admin.ModelAdmin):
    list_display = ('dataResenha', 'nomeAluno', 'nomelivro')


@admin.register(PeriodoLeitura)
class IntervaloLeitura(admin.ModelAdmin):
    pass