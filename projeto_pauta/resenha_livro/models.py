from django.db import models
from django.utils import timezone
import re

class Turma(models.Model):
    nome = models.CharField('Nome da Turma:', max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = 'turma'
        verbose_name_plural = 'Adicionar turmas'

    def __str__(self):
        return self.nome

class PeriodoLeitura(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='periodos')
    intervalo_leitura = models.CharField('Periodo de leitura:', max_length=30, blank=False, null=False)
    data_resenha = models.DateField('Data da Resenha:', blank=False, null=False)

    class Meta:
        verbose_name = 'periodo de leitura'
        verbose_name_plural = 'Adicionar periodos de leituras'

    def __str__(self):
        return f'{self.turma.nome} - {self.intervalo_leitura} - {self.data_resenha.strftime("%d/%m/%Y")}'

class Aluno(models.Model):
    nome = models.CharField('Nome do Aluno:', max_length=100, blank=False, null=False)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')

    class Meta:
        verbose_name = 'aluno'
        verbose_name_plural = 'Adicionar alunos'

    def __str__(self):
        return self.nome

class ResenhaLivro(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='resenhas')
    nomelivro = models.CharField('Obra:', max_length=200, blank=False, null=False)
    nomeAutor = models.CharField('Autor:', max_length=100, blank=False, null=False)
    periodoLeitura = models.ForeignKey(PeriodoLeitura, on_delete=models.CASCADE, related_name='resenhas')
    nomeProfessor = models.CharField('Nome do professor(a):', max_length=150, blank=False, null=False, default='Terlene Bolzan')

    def __str__(self):
        return f'{self.aluno.nome} - {self.nomelivro}'

    @property
    def dataResenha(self):
        return self.periodoLeitura.data_resenha

    class Meta:
        ordering = ('aluno',)
        verbose_name = 'resenha de livro'
        verbose_name_plural = 'Adicionar resenhas de livros'

    def format_data_resenha(self):
        if self.dataResenha:
            return self.dataResenha.strftime('%d/%m/%Y')
    format_data_resenha.short_description = 'Data da Resenha'