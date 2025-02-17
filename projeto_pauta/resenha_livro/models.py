from django.db import models
from django.utils import timezone


# Create your models here.

class ResenhaLivro(models.Model):
    
    periodosLeituras = (
        ('12/02/2025 até 10/03/2025' , '12/02/2025 até 10/03/2025'),
        ('12/12/2025 até 10/03/2026' , '12/02/2025 até 10/03/2025')
    )

    profe = (
        ('Terlene bolzano', 'Terlene bolzano')
    )

    dta_resenha = '10/03/2025'
    nomeAluno = models.CharField('Aluno:', max_length=100, blank=True, null=True)
    nomelivro = models.CharField('Obra:', max_length=200, blank=False, null=False)
    nomeAutor = models.CharField('Autor:', max_length=100, blank=False, null=False)
    periiodoLeitura = models.CharField('Periodo de leitura:',max_length=30, choices=periodosLeituras, blank=False, null=False, default=periodosLeituras[0])
    dataResenha = models.DateField('Data da Resenha:', blank=False, null=False, default=dta_resenha)
    nomeProfessor = models.CharField('Nome do prefoessor(a):', max_length=150, blank=False, null=False, default=profe[0])


    def __str__(self):
        return self.dataResenha
    
    def format_data_resenha(self):
        if self.dataResenha:
            return self.format_dataResenha('%d/%m/%y')
    format_data_resenha.short_description = 'Data da Resenha'