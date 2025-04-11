from django.contrib import admin
from .models import ResenhaLivro, PeriodoLeitura, Turma, Aluno

@admin.register(ResenhaLivro)
class ResenhaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'nomelivro', 'nomeAutor', 'periodoLeitura', 'format_data_resenha', 'nomeProfessor')
    list_filter = ('aluno',)
    search_fields = ('nomelivro', 'nomeAutor', 'nomeProfessor')

@admin.register(PeriodoLeitura)
class PeriodoLeituraAdmin(admin.ModelAdmin):
    list_display = ('turma', 'intervalo_leitura', 'data_resenha')

@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome',)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'turma')