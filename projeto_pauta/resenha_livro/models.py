from django.db import models
from django.utils import timezone
import re


# Create your models here.

class ResenhaLivro(models.Model):
    @property
    def get_data_resenha(self):
        dta_resenha_tuple = re.findall(r'\d{2}/\d{2}/\d[4]', self.periodosLeituras[0])
        if dta_resenha_tuple:
            dta_real = dta_resenha_tuple[-1]
            return dta_real
        return None
    
    periodosLeituras = (
        ('12/02/2025 até 10/03/2025' , '12/02/2025 até 10/03/2025'),
        ('12/12/2025 até 10/03/2026' , '12/02/2025 até 10/03/2025')
    )

    profe = (
        ('Terlene bolzano', 'Terlene bolzano')
    )

    #dta_resenha = '10/03/2025'
    


    nomeAluno = models.CharField('Aluno:', max_length=100, blank=True, null=True)
    nomelivro = models.CharField('Obra:', max_length=200, blank=False, null=False)
    nomeAutor = models.CharField('Autor:', max_length=100, blank=False, null=False)
    periiodoLeitura = models.CharField('Periodo de leitura:',max_length=30, choices=periodosLeituras, blank=False, null=False, default=periodosLeituras[0])
    dataResenha = models.DateField('Data da Resenha:', blank=False, null=False, default=get_data_resenha)
    nomeProfessor = models.CharField('Nome do prefoessor(a):', max_length=150, blank=False, null=False, default=profe[0])


    def __str__(self):
        return self.nomeAluno
    
    
    

    def format_data_resenha(self):
        if self.dataResenha:
            return self.format_dataResenha('%d/%m/%y')
    format_data_resenha.short_description = 'Data da Resenha'

class PeriodoLeitura(models.Model):
    intervalo_leitura = models.CharField('Periodo de leitura:', max_length=30, blank=False, null=False)